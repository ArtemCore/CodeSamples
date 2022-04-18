from typing import Dict, List, Tuple

from bson import ObjectId

from Model.enums import Channel, ItemType
from Model.product import Product, ProductCategory
from POSSystems.BasePOS.POSParser import POSParser
from POSSystems.R.RConstants import r_PRICE_DECIMALS, RProps
from POSSystems.R.RModel import (
    RWebMenu,
    RWebMenuCategory,
    RWebMenuProduct,
    RWebMenuProductModifierClass,
    RWebMenuProductModifierClassModifiers,
)


class RProductParserV2(POSParser):
    def __init__(self, logger, defaultTax):
        super().__init__()
        self.logger = logger
        self.defaultTax = defaultTax
        self.categoryById: Dict[int, ProductCategory] = {}
        self.productsByPLU: Dict[str, Product] = {}
        self.modGroupByPLU: Dict[str, Product] = {}
        self.modifierByPLU: Dict[str, Product] = {}
        self.overloadedProducts: List[Product] = []

    def parseProductsToDc(self, rawMenu: Dict) -> Tuple[List[Product], List[ProductCategory]]:
        rMenu: RWebMenu = RWebMenu.parse_obj(rawMenu)
        for rCategory in rMenu.categories:
            self.createCategory(rCategory)
            for rProduct in rCategory.products:
                self.createProduct(rProduct)
        products: List[Product] = list(self.productsByPLU.values())
        products.extend(list(self.modGroupByPLU.values()))
        products.extend(list(self.modifierByPLU.values()))
        products.extend(self.overloadedProducts)
        return products, list(self.categoryById.values())

    def createCategory(self, rCategory: RWebMenuCategory) -> ProductCategory:
        category: ProductCategory = ProductCategory()
        category.name = rCategory.name
        category.posCategoryId = rCategory.id
        category.channel = Channel.POS
        self.categoryById[category.posCategoryId] = category
        return category

    def createProduct(self, rProduct: RWebMenuProduct) -> Product:
        product: Product = Product()
        product.categoryId = rProduct.id_category
        plu = rProduct.sku or rProduct.barcode
        if not plu:
            self.logger.warning(f"{rProduct.name} does not have barcode or sku. Excluded from synchronization")
            return
        product.plu = plu
        product.name = rProduct.name
        product.description = rProduct.description
        product.posProductId = rProduct.id
        if rProduct.is_combo:
            product.isCombo = True
        if rProduct.image:
            product.imageUrl = rProduct.image
        product.productType = ItemType.PRODUCT
        product.deliveryTax = product.takeawayTax = product.eatInTax = self.defaultTax
        product.price = self.getPriceFromPos(rProduct.price, r_PRICE_DECIMALS)

        product.setPosProp(RProps.RESOURCE_URI, f"/resources/Product/{rProduct.id}")

        for rModGroup in rProduct.modifier_classes:
            modGroup: Product = self.createModGroup(rModGroup)
            for rModifier in rModGroup.modifiers:
                modifier: Product = self.createModifier(rModifier)
                modGroup.subProducts.append(modifier)
            product.subProducts.append(modGroup)
        self.productsByPLU[product.plu] = product

    def createModGroup(self, rModGroup: RWebMenuProductModifierClass) -> Product:
        if existingModGroup := self.modGroupByPLU.get(f"{rModGroup.modifier_class_id}-MG"):
            if (
                not existingModGroup.min == rModGroup.minimum_amount
                or not existingModGroup.max == rModGroup.maximum_amount
                or sorted([m.id for m in rModGroup.modifiers])
                != sorted([m.plu for m in existingModGroup.subProducts])
            ):
                modifierGroup = existingModGroup.copy()
                modifierGroup._id = ObjectId()
                existingModGroup.min = rModGroup.minimum_amount
                existingModGroup.max = rModGroup.maximum_amount
                self.overloadedProducts.append(modifierGroup)
                return modifierGroup
            return existingModGroup
        modifierGroup = Product()
        modifierGroup.plu = f"{rModGroup.modifier_class_id}-MG"
        modifierGroup.name = rModGroup.name
        modifierGroup.posProductId = rModGroup.id
        modifierGroup.min = rModGroup.minimum_amount
        modifierGroup.max = rModGroup.maximum_amount
        modifierGroup.productType = ItemType.MODIFIER_GROUP
        self.modGroupByPLU[modifierGroup.plu] = modifierGroup
        return modifierGroup

    def createModifier(self, rModifier: RWebMenuProductModifierClassModifiers) -> Product:
        if existingModifier := self.modifierByPLU.get(f"{rModifier.id}-M"):
            if self.getPriceFromPos(existingModifier.price) != self.getPriceFromPos(rModifier.price):
                modifier = existingModifier.copy()
                modifier._id = ObjectId()
                modifier.price = self.getPriceFromPos(rModifier.price)
                self.overloadedProducts.append(modifier)
                return modifier
            return existingModifier
        modifier: Product = Product()
        modifier.plu = f"{rModifier.id}-M"
        modifier.name = rModifier.name
        modifier.posProductId = rModifier.id
        modifier.productType = ItemType.MODIFIER
        modifier.price = self.getPriceFromPos(rModifier.price)
        self.modifierByPLU[modifier.plu] = modifier
        return modifier
