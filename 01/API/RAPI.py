# stdlib
import urllib
from http import HTTPStatus
from multiprocessing.pool import ThreadPool
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import parse_qs

# third party
from dacite import from_dict
from exceptions import (BusinessClosed, InvalidPOSAPIResult,
                        InvalidPOSConfiguration, OutOfStockException,
                        UnexpectedPOSException)
from Middleware.Context import Context
from Middleware.DCModel import (Account, ChannelLink, Customer, Location,
                                Order, OrderStatus, OrderStatusUpdate)
from Model.enums import POS, RequestType
from Model.integration import IntegrationInfo, POSHealthCheckResult
from Model.operationReport import OperationReportStatus
from Model.product import ProductSyncInfo, ProductSyncSettings
from Model.settings import (AppStoreActionSettingsResponse, GenericSetting,
                            ValidateSettingsResponse)
from POSSystems.BasePOS.BasePOSAPI import BasePOSAPI
from POSSystems.R.RConstants import (CHUNK_LIMIT, DC_DELIVERY_FEE_KEY,
                                     DC_DISCOUNT_BARCODE, DC_DISCOUNT_NAME,
                                     DC_SERVICE_CHARGE_KEY, DC_SERVICE_FEE_MAP,
                                     R_LIMIT, R_NEW_API_URL,
                                     R_PREVAILING_TAX_SETTING_NAME,
                                     RApiMethods, RApiVersion)
from POSSystems.R.RModel import (RAPICustomPaymentType, RAPIObject, RAPIUser,
                                 RCustomMenu, RCustomPaymentType, RDiscount,
                                 RDynamicCombo, REstablishment, RFloor,
                                 RPrevailingTax, RProduct, RProductAttribute,
                                 RProductGroup, RProductModifier,
                                 RProductModifierGroup, RProductModifierInfo,
                                 RProductTaxGroup, RServiceFee, RTable, RUser,
                                 RWebOrder)
from POSSystems.R.RParser import RParser
from POSSystems.R.setup import (VALIDATE_REQUIRED_SETTINGS_MAPPING, RSettings,
                                getCallNameTemplateSetting,
                                getConnectionSettings, getCountrySetting,
                                getCustomCashPaymentTypeSetting,
                                getCustomMenuSetting, getDefaultTaxRateSetting,
                                getDeliveryDiningOptionSetting,
                                getDeliveryFeeAliasSetting,
                                getDiscountBarcodeSetting,
                                getEatInDiningOptionSetting,
                                getEstablishmentSetting,
                                getModifierTaxRateOverrideSetting,
                                getPaymentTypeSetting,
                                getPickupDiningOptionSetting,
                                getServiceChargeAliasSetting,
                                getUseOverloadsSetting,
                                getUseProductSyncV2Setting, getUserSetting,
                                getUseSlowSyncSetting, getUseVariantSetting,
                                getUseWebOrderMenuSetting)
from settings import (DOMAIN_URL, R_CONNECT_TIMEOUT_IN_SECONDS,
                      R_READ_TIMEOUT_IN_SECONDS)
from Utilities import isReachable, returnOnFailure
from Utilities.helpers import chunks, validateEmail
from Utilities.settings import convertSecretFieldsToPasswordType

# inhouse



class RAPI(BasePOSAPI):
    """
    R POS API
    api docs url here
    """

    pos = POS.R
    settingsType = RSettings
    settings: RSettings

    sequentialSyncAccountProducts = True
    supportsBufferedOrders = True
    autoAcceptsOrders = True
    supportsInternalProducts = True
    supportInternalProductModifiers = True
    supportsOrderNoteTemplate = True
    supportsTips = True
    showEnforceCustomerInfoSetting = True
    bufferOrdersOnBusinessClosed = True
    supportsDeliveryByResto = True
    supportsEatInOrders = True
    supportsGetTables = True
    supportsHealthCheck = True
    # R orders require establishment specific product IDs
    supportsProductLocation = False
    supportsSnoozeTime = True

    def __init__(
        self,
        source: Union[Account, Location, ChannelLink] = None,
        account: Optional[Account] = None,
        location: Optional[Location] = None,
        channelLink: Optional[ChannelLink] = None,
        posSystemId: Optional[int] = None,
    ):
        super(RAPI, self).__init__(
            source=source,
            account=account,
            location=location,
            channelLink=channelLink,
            posSystemId=posSystemId,
        )
        self.parser = RParser(self.logger, self.settings)

        self.endpointUrl: str = f"{R_NEW_API_URL}{RApiVersion.v0}/"
        self.apiKey: str = self.settings.apiKey
        self.secretKey: str = self.settings.secretKey
        self.establishment: str = self.settings.establishment
        self.user: str = self.settings.user
        self.discountBarcode: str = self.settings.discountBarcode
        self.deliveryFeeAlias: str = self.settings.deliveryFeeAlias
        self.serviceChargeAlias: str = self.settings.serviceChargeAlias
        self.customMenuUri: str = self.settings.customMenuUri
        self.useSlowSync: bool = self.settings.useSlowSync
        # need to get id from resourceUri (eg. /resources/Establishment/1/) to filter by establishmentId
        self.establishmentId = None
        if self.establishment:
            try:
                self.establishmentId = int(
                    self.establishment.split("/")[-2]
                )  # trailing slash in resourceUri
            except (SyntaxError, IndexError, ValueError):
                self.logger.error(
                    f"Unexpected resourceUri format: {self.establishment}"
                )

        self.expectedDiscountName: str = ""
        self.expectedDiscountBarcode: str = ""
        self.expectedServiceChargeName: str = ""
        self.expectedServiceChargeAlias: str = ""
        self.expectedDeliveryFeeName: str = ""
        self.expectedDeliveryFeeAlias: str = ""
        if self.channelLink:
            # Discount/ServiceFee names will be displayed in app
            channelLinkName = self.channelLink.channel.name
            self.expectedDiscountName = f"{channelLinkName} {DC_DISCOUNT_NAME}"
            # discount barcode maxLength=16
            self.expectedDiscountBarcode = f"{channelLinkName.replace('_', '-')}-{DC_DISCOUNT_BARCODE}"[
                :16
            ]
            (
                self.expectedServiceChargeName,
                self.expectedServiceChargeAlias,
            ) = self._getServiceFeeItemNameAndAlias(DC_SERVICE_CHARGE_KEY)
            (
                self.expectedDeliveryFeeName,
                self.expectedDeliveryFeeAlias,
            ) = self._getServiceFeeItemNameAndAlias(DC_DELIVERY_FEE_KEY)

    def _callPOSAPI(self, method: RequestType, route: str, **kwargs):
        """
        Performs a request to the POS. It handles all authentication logic and parses errors
        :param method: the type of request (POST/PATCH/GET/DELETE)
        :param route: the route to be called
        :return: returns a response from the POS
        """

        clientId = self.settings.clientID

        if not all([self.settings.clientID, self.apiKey, self.secretKey]):
            raise InvalidPOSConfiguration(
                "R POS setup isn't completed, please define all settings."
            )

        headers = {
            "API-AUTHENTICATION": f"{self.apiKey}:{self.secretKey}",
        }
        if "headers" in kwargs:
            kwargs["headers"].update(headers)
        else:
            kwargs["headers"] = headers
        # R is very slow on inserting orders, but for some accounts even the product sync pagination takes ages
        if clientId:
            kwargs["headers"]["Client-Id"] = clientId

        if R_CONNECT_TIMEOUT_IN_SECONDS and R_READ_TIMEOUT_IN_SECONDS:
            kwargs["timeout"] = (
                R_CONNECT_TIMEOUT_IN_SECONDS,
                R_READ_TIMEOUT_IN_SECONDS,
            )

        response = super()._callPOSAPI(method, route, **kwargs)
        # check response codes of call
        if response.status_code in [
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.NOT_FOUND,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.BAD_REQUEST,
        ]:
            raise InvalidPOSAPIResult(
                HTTPResponse=str(response.status_code), message=response.text,
            )
        return response

    @classmethod
    @convertSecretFieldsToPasswordType
    def getBasicSettings(cls, account: Account) -> List[GenericSetting]:
        """Get basic settings to setup a R POS"""
        settings: List[GenericSetting] = getConnectionSettings()
        return settings

    def verifyCreds(self) -> bool:
        """
        call simply method to check if creds are valid
        :return:
        """
        isValid: bool = True
        try:
            self._getEstablishmentsInfo()
        except (InvalidPOSAPIResult, UnexpectedPOSException, InvalidPOSConfiguration):
            self.logger.warning(
                f"Invalid credentials for R location #{self.location.oid}"
            )
            isValid = False
        return isValid

    def _getEstablishmentsInfo(self) -> Dict:
        params = {"limit": R_LIMIT}
        route: str = RApiMethods.ESTABLISHMENTS
        result = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        rEstablishmentsInfo: Dict = result.json()

        return rEstablishmentsInfo

    @returnOnFailure([])
    def getCustomMenus(self) -> List[RAPIObject]:
        """Get Custom Menus from R POS"""
        params = {
            "active": True,
            "establishment": self.establishmentId,
            "fields": "name",
        }
        route: str = RApiMethods.CUSTOM_MENU

        menus = self._getAllPOSResults(route, params=params)
        menus = [from_dict(RAPIObject, menu) for menu in menus]
        return menus

    def getProductSyncInfo(self, syncSettings: ProductSyncSettings) -> ProductSyncInfo:
        """
        Return a tuple with a list of all productCategories and a list with Products
        :return:
        """
        callback = False
        if self.settings.useWebOrderMenu:
            operationReport = Context.operationReport
            operationReport.setOperationStatus(OperationReportStatus.AWAIT)
            clientId = self.settings.clientID
            params = {"establishment": self.establishmentId}
            route = f"{R_NEW_API_URL}{RApiVersion.v0}{RApiMethods.WEBORDERS_MENU}"
            headers = {
                "Callback-Url": urllib.parse.urljoin(
                    DOMAIN_URL, f"/r/menu/{operationReport.oid}"
                ),
                "Client-Id": clientId,
            }
            response = self._callPOSAPI(
                method=RequestType.GET, route=route, headers=headers, params=params
            )
            correlationId: str = response.headers.get("Correlation-Id")
            reportProperties: Dict = {
                "forceUpdate": syncSettings.forceUpdate,
                "preview": syncSettings.preview,
                "correlationId": correlationId,
                "defaultTax": self.settings.defaultTaxRate,  # just to skip loading posSettings in route add tax here
            }
            operationReport.properties = reportProperties
            products = productCategories = []
            callback = True
        else:
            if self.customMenuUri:
                self.logger.info(
                    f"Start Product sync for Custom Menu: {self.customMenuUri}"
                )
                products = self._getPOSProductsWithCategoryCustomMenu()
            else:
                self.logger.info(f"Start Product sync for {self.channelLink}")
                products = self._getPOSProductsWithCategory()
            self.logger.info(f"Got {len(products)} R products")

            # TODO: speedup this step.
            productModifiers = self._getPOSProductModifiers()
            self.logger.info(f"Got {len(productModifiers)} R product modifiers")

            productTaxGroups = self._getPOSProductTaxGroups()
            self.logger.info(f"Got {len(productTaxGroups)} R tax groups")

            # getting prevailing tax
            prevailingTax = self._getPOSPrevailingTax()
            self.logger.info(f"Got prevailing tax")

            modifierGroups = self._getPOSModifierGroups()
            self.logger.info(f"Got {len(modifierGroups)} R modifier groups")

            modifiers = self._getPOSModifiers()
            self.logger.info(f"Got {len(modifiers)} R modifiers")

            dynamicCombos = self._getPOSDynamicComboItems()
            self.logger.info(f"Got {len(dynamicCombos)} R DynamicCombos")

            productAttributes = self._getProductAttrs()
            self.logger.info(f"Got {len(productAttributes)} R Product Attributes")

            productAttributeValues = self._getProductAttrValues()
            self.logger.info(
                f"Got {len(productAttributeValues)} R Product Attribute Values"
            )

            products, productCategories = self.parser.parseProducts(
                products,
                productModifiers,
                productTaxGroups,
                prevailingTax,
                modifierGroups,
                modifiers,
                dynamicCombos,
                productAttributes,
                productAttributeValues,
            )

        return ProductSyncInfo(
            categories=productCategories,
            products=products,
            syncOverloads=self.settings.useOverloads,
            callback=callback,
        )

    def _getPOSCustomMenu(self) -> RCustomMenu:
        """
        Gets R custom menu objects with corresponding product group
        :return
        """
        route: str = self.prepareRoute(self.customMenuUri)

        params = {"expand": "product_group"}
        response = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        rawCustomMenu: Dict[str, Any] = response.json()
        rCustomMenu: RCustomMenu = RCustomMenu.importDict(rawCustomMenu)
        return rCustomMenu

    def _getPOSProductGroup(self, rCustomMenu: RCustomMenu) -> RProductGroup:
        """
        Gets R product group with list of products uri
        :return
        """
        route: str = self.prepareRoute(rCustomMenu.productGroupUri)
        params = {"active": True}
        response = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        rawRProductGroup: Dict[str, Any] = response.json()
        rProductGroup: RProductGroup = RProductGroup.importDict(rawRProductGroup)
        return rProductGroup

    def _getPOSCustomMenuProduct(self, route: str) -> RProduct:
        """
        Gets R product from Custom menu
        :return
        """
        params = {
            "expand": "category",
            "active": True,
            "establishment": self.establishmentId,
        }

        response = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        rawCustomMenuProduct: Dict[str, Any] = response.json()
        rCustomMenuProduct = RProduct.importDict(rawCustomMenuProduct)
        return rCustomMenuProduct

    def _getPOSProductsWithCategoryCustomMenu(self) -> List[RProduct]:
        """
        R allows compose custom menu with a set of products
        We use custom menu uri to retrieve product groups with the list of uri of the products included
        Call for every product with expand on category info
        Since no info on modifier groups or modifiers provided,
        we still need to retrieve all of them in basic sync products flow
        :return
        """
        rCustomMenu: RCustomMenu = self._getPOSCustomMenu()
        rProductGroup: RProductGroup = self._getPOSProductGroup(rCustomMenu)

        if rProductGroup.establishment != self.establishment:
            raise InvalidPOSConfiguration(
                message=f"Custom menu establishment {rProductGroup.establishment} "
                f"doesn't match location establishment {self.establishment}"
            )
        productIds: List[str] = []
        for productUri in rProductGroup.productsUri:
            productId: str = productUri.split("/")[-2]
            productIds.append(productId)
        route: str = RApiMethods.PRODUCT

        rawRProducts: List[Dict] = []
        # prevent 414 - URI too long error
        for chunk in chunks(productIds, CHUNK_LIMIT):
            params: Dict = {
                "expand": "category",
                "active": True,
                "establishment": self.establishmentId,
                "id__in": ",".join(chunk),
            }
            rawRProducts.extend(self._getAllPOSResults(route, params))

        # load them in the model
        rCustomMenuProducts: List = [
            RProduct.importDict(rProduct) for rProduct in rawRProducts
        ]

        if not rCustomMenuProducts:
            raise InvalidPOSAPIResult(
                message=f"No products found for {rProductGroup.name}"
            )
        return rCustomMenuProducts

    def _getPOSProductsWithCategory(self) -> List[RProduct]:
        """
        Get a list of all products with categories.
        By default, R doesn't provide information about the product category,
        but with the help of the query parameter we expand the response.
        :return: the list of all products with categories
        """
        route: str = RApiMethods.PRODUCT

        params = {
            "expand": "category",
            "active": True,
            "establishment": self.establishmentId,
        }

        # get all product objects from R
        totalRProductResults = self._getAllPOSResults(route, params)

        rProducts = [RProduct.importDict(product) for product in totalRProductResults]
        return rProducts

    def _getPOSModifiers(self) -> List[RProductModifier]:
        """
        Get a list of all R modifiers. The query is needed to create standard modifier groups.
        :return: the list of all R modifiers
        """
        route: str = RApiMethods.MODIFIER

        params = {
            "expand": "modifierClass",
            "active": True,
            "establishment": self.establishmentId,
        }

        # get all modifier objects from R
        totalRModifierResults = self._getAllPOSResults(route, params)

        rModifiers: List = [
            RProductModifier.importDict(rModifier)
            for rModifier in totalRModifierResults
        ]

        return rModifiers

    def _getPOSProductModifiers(self) -> List[RProductModifierInfo]:
        """
        Get a list of R product modifiers.
        The query is needed to obtain a product link with a modifier.
        :return: the list of R product modifiers
        """
        route: str = RApiMethods.PRODUCT_MODIFIER

        params = {
            "expand": "modifier,product_modifier_class",
            "modifier__active": True,
            "product__active": True,
            "modifier__establishment": self.establishmentId,
        }

        # get all modifier objects from R
        totalRModifierResults = self._getAllPOSResults(route, params)

        rProductModifiers: List = [
            RProductModifierInfo.importDict(rModifier)
            for rModifier in totalRModifierResults
        ]
        return rProductModifiers

    def _getPOSModifierGroups(self) -> List[RProductModifierGroup]:
        """
        Get a list of all R modifier groups(classes).
        :return: the list of all R modifier groups(classes)
        """

        route: str = RApiMethods.MODIFIER_CLASS

        params = {"establishment": self.establishmentId}

        # get all modifier group objects from R
        totalRModifierGroupResults = self._getAllPOSResults(route, params)

        rModifierGroups: List = [
            RProductModifierGroup.importDict(group)
            for group in totalRModifierGroupResults
        ]

        return rModifierGroups

    def _getPOSDynamicComboItems(self) -> List[RDynamicCombo]:
        """
        Get a list of all dynamic combos.
        :return: the list of all dynamic combos
        """
        route: str = RApiMethods.DYNAMIC_COMBO

        params = {"establishment": self.establishmentId}

        totalRDynamicCombosResults = self._getAllPOSResults(route, params)

        rDynamicCombos = [
            RDynamicCombo.importDict(product) for product in totalRDynamicCombosResults
        ]
        return [combo for combo in rDynamicCombos if combo.active]

    def _getPOSPrevailingTax(self) -> RPrevailingTax:
        """Get prevailing tax from POS settings"""

        # a SystemSettingOption belongs to a SystemSetting
        # we must filter by SystemSetting resource_uri ID, because it can be different from as establishment

        # get SystemSetting for establishment
        params = {
            "establishment": self.establishmentId,
            "fields": "establishment",
        }  # limit the returned data
        response = self._callPOSAPI(
            method=RequestType.GET, route=RApiMethods.SYSTEM_SETTING, params=params
        )
        if not response.ok or not response.json().get("objects"):
            self.parser.report(
                "ERROR", f"Failed to get system settings: {response.text}"
            )
            raise InvalidPOSAPIResult(
                f"Failed to load system settings for establishment {self.establishment}"
            )
        systemSettingResourceUri = response.json().get("objects")[0]["resource_uri"]
        # get the number in /resources/SystemSetting/1/
        systemSettingResourceId = int(systemSettingResourceUri.split("/")[-2])

        # get SystemSettingOption for this SystemSetting
        route: str = RApiMethods.SYSTEM_SETTING_OPTION
        params = {
            "setting_name": R_PREVAILING_TAX_SETTING_NAME,
            "settings_parent": systemSettingResourceId,
        }
        rawResult = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        if not response.ok or not response.json().get("objects"):
            self.parser.report(
                "ERROR", f"Failed to get prevailing tax settings: {response.text}"
            )
            raise InvalidPOSAPIResult(
                f"Failed to load prevailing tax for establishment {self.establishment}"
            )
        rPrevailingTax = RPrevailingTax.importDict(rawResult.json().get("objects")[0])

        return rPrevailingTax

    def _getPOSProductTaxGroups(self) -> List[RProductTaxGroup]:
        """
        Get a list of all R tax groups.
        :return: the list of all R tax groups
        """

        route: str = RApiMethods.TAX_PRODUCT_GROUP

        params = {"establishment": self.establishmentId}

        # get all tax group objects from R
        totalRProductTaxGroupResults = self._getAllPOSResults(route, params)

        rProductTaxGroups = [
            RProductTaxGroup.importDict(group) for group in totalRProductTaxGroupResults
        ]

        return rProductTaxGroups

    def _getProductAttrs(self) -> List[RProductAttribute]:
        """
        The Attribute resource holds information about a product's particular attributes,
        including the product's name, unique ID, creation date, and active or inactive status.
        :return: the list of all R product attributes for current establisment
        """

        route: str = RApiMethods.ATTRIBUTE

        params = {"establishment": self.establishmentId}

        # get all tax group objects from R
        totalRProductAttrsResults = self._getAllPOSResults(route, params)

        rProductAttrs: List[RProductAttribute] = [
            RProductAttribute.importDict(attr) for attr in totalRProductAttrsResults
        ]

        return rProductAttrs

    def _getProductAttrValues(self) -> List[RProductAttribute]:
        """
        The AttributeValue resource lets you access and manage data about the values of product attributes.
        This includes Boolean values like active/inactive as well as date and string data.
        :return: the list of all R Product attribute values for this establishment
        """

        route: str = RApiMethods.ATTRIBUTE_VALUE

        params = {"establishment": self.establishmentId}

        # get all tax group objects from R
        totalRProductAttrsResults = self._getAllPOSResults(route, params)

        rProductAttrs: List[RProductAttribute] = [
            RProductAttribute.importDict(attr) for attr in totalRProductAttrsResults
        ]

        return rProductAttrs

    def _getAllPOSResults(self, route: str, params: Dict) -> List[Dict]:
        """
        Get a list of all objects from R.
        :param params: dictionary of method params
        :return:  returns the list of all objects for R API method
        """
        params["limit"] = R_LIMIT

        rawResult = self._callPOSAPI(method=RequestType.GET, route=route, params=params)

        rawResultJson = rawResult.json()

        totalRObjectResults = rawResultJson.get("objects")

        totalCount = rawResultJson.get("meta", {}).get("total_count", 0)

        if self.useSlowSync:
            nextPage = rawResultJson.get("meta", {}).get("next", None)
            while nextPage:
                self.logger.info(nextPage)
                offset = parse_qs(nextPage).get("offset")[0]
                params["offset"] = offset
                rawResult = self._callPOSAPI(
                    method=RequestType.GET, route=route, params=params
                )
                rawResultJson = rawResult.json()
                totalRObjectResults.extend(rawResultJson.get("objects"))
                nextPage = rawResultJson.get("meta", {}).get("next", None)
        else:
            if totalCount > R_LIMIT:
                callParams = []
                for offset in range(R_LIMIT, totalCount, R_LIMIT):
                    # extend call params with offset
                    extParams = dict(params)
                    extParams["offset"] = offset
                    callParams.append((route, extParams))
                # get all results in parallel
                totalResult = self._parallelMap(self._getPOSObjects, callParams)

                for result in totalResult:
                    totalRObjectResults.extend(result)

        return totalRObjectResults

    def _getPOSObjects(self, route, params) -> List[Dict]:
        """Get objects from POS with offset"""
        response = self._callPOSAPI(method=RequestType.GET, route=route, params=params)
        return response.json().get("objects")

    @staticmethod
    def _parallelMap(executable: Callable, iterable: Iterable) -> List:
        with ThreadPool(2) as threadPool:
            result = threadPool.starmap(executable, iterable)
        return result

    def healthCheck(self) -> POSHealthCheckResult:
        result: POSHealthCheckResult = POSHealthCheckResult()
        if self._validateConnectionSettings() is None:
            # All connection settings are set, check if are valid.
            try:
                self._callPOSAPI(RequestType.GET, RApiMethods.TABLES)
                result.sampleCallOK = result.credentialsOK = result.connectionOK = True
                result.sampleCallResponse = f"Successfully called {self.pos.name} API"
                result.credentialsResponse = "Credentials are valid"
                result.connectionResponse = f"Successfully connected to {self.pos.name}"
            except InvalidPOSAPIResult:
                result.sampleCallResponse = (
                    "Invalid POS API Result : Invalid credentials"
                )
                result.credentialsResponse = "Credentials are set, but are invalid"
                result.connectionResponse = (
                    "Invalid POS API Result : Invalid credentials"
                )
            # we have more errors in _callPOSAPI, but those are not going to raise because they are for
            # 201 http responses (no json inside the response)
        else:
            # Some connection settings are missing
            result.sampleCallResponse = f"Could not call to {self.pos.name} because some credentials are missing or invalid"
            result.credentialsResponse = "Some credentials are missing or invalid"
            result.connectionResponse = f"Could not connect to {self.pos.name} because some credentials are missing or invalid"
        return result
