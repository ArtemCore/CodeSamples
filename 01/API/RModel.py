from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from POSSystems.BasePOS.POSModel import POSModel, posfield, posmodel


@posmodel
class RAPIObject:
    """
    Get by API call
    """

    name: str = ""
    resource_uri: str = ""


@posmodel
class RAPIUser:
    """
    Get by API call
    """

    first_name: str = ""
    last_name: str = ""
    username: str = ""
    resource_uri: str = ""

    def getUserName(self):
        firstName = self.first_name
        lastName = self.last_name
        name = f"{firstName} {lastName}"
        if not name.strip():
            name = self.username

        return name


@posmodel
class RAPICustomPaymentType:
    """
    Get by API call
    """

    active: bool = False
    is_public: bool = False
    name: str = ""
    payment_id: int = 0


@posmodel
class REstablishment:
    objects: List[RAPIObject]


@posmodel
class RUser:
    objects: List[RAPIUser]


@posmodel
class RCustomPaymentType:
    objects: List[RAPICustomPaymentType]


@posmodel
class RProductCategory(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")


@posmodel
class RProductProductSet(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    quantity: int = posfield(property="quantity")

    # product = R product resource uri
    products: List[str] = posfield(property="products")


@posmodel
class RProductTaxRate(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    taxRate: str = posfield(property="tax_rate")
    effectiveTo: str = posfield(property="effective_to")
    effectiveFrom: str = posfield(property="effective_from")


@posmodel
class RProductTax(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    # tax rate object
    taxRate: List[RProductTaxRate] = posfield(property="tax_rate")
    diningOptions: str = posfield(property="dining_options")


@posmodel
class RProductGroup(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    resourceUri: str = posfield(property="resource_uri")
    productsUri: List[str] = posfield(property="products", default_factory=list)
    establishment: str = posfield(property="establishment")


@posmodel
class RCustomMenu(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    resourceUri: str = posfield(property="resource_uri")
    productGroupUri: str = posfield(property="product_group", importFunc=lambda x: x.get("resource_uri"))


@posmodel
class RUpsellComboDetail(POSModel):
    upsellCombo: str = posfield(property="upsell_combo")
    upsellComboPrice: float = posfield(property="upsell_combo_price", importFunc=lambda x: float(x), default=0.0)
    sorting: int = posfield(property="sorting")


@posmodel
class RProduct(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    isCombo: bool = posfield(property="is_combo")
    sku: str = posfield(property="sku")
    barcode: str = posfield(property="barcode")
    name: str = posfield(property="name")
    price: float = posfield(property="price")
    category: RProductCategory = posfield(property="category")
    resourceUri: str = posfield(property="resource_uri")
    uuid: str = posfield(property="uuid")
    imageUrl: str = posfield(property="image")
    description: str = posfield(property="description")
    dynamicCombo: str = posfield(property="dynamic_combo")
    productGroup: List[str] = posfield(property="product_group")
    tax: RProductTax = posfield(property="tax")
    combo_upcharge: float = posfield(property="combo_upcharge", importFunc=lambda x: float(x), default=0.0)
    upsell_combo_price: float = posfield(property="upsell_combo_price", importFunc=lambda x: float(x), default=0.0)
    sold_by_weight: bool = posfield(property="sold_by_weight")
    attribute_type: str = posfield(property="attribute_type")
    attribute_parent: str = posfield(property="attribute_parent")
    attribute: str = posfield(property="attribute_1")
    attribute2: str = posfield(property="attribute_2")
    attributeValue: str = posfield(property="attribute_value_1")
    attributeValue2: str = posfield(property="attribute_value_2")
    # product sets list in combo product
    comboProductSets: List[RProductProductSet] = posfield(property="combo_productsets")
    upsellCombos: List[RUpsellComboDetail] = posfield(property="upsell_combos", default_factory=list)


@posmodel
class RProductModifierGroup(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    resourceUri: str = posfield(property="resource_uri")


@posmodel
class RProductModifierGroupInfo(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    # resource uri of product modifier class
    resourceUri: str = posfield(property="resource_uri")
    # resource uri of R Product
    product: str = posfield(property="product")
    description: str = posfield(property="description")
    minModifierPerGroup: int = posfield(property="forced")
    maxModifierPerGroup: int = posfield(property="lock_amount")
    modifierClass: str = posfield(property="modifierclass")


@posmodel
class RProductModifier(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    price: float = posfield(property="price")
    sku: str = posfield(property="sku")
    uuid: str = posfield(property="uuid")
    resourceUri: str = posfield(property="resource_uri")
    modifierClass: RProductModifierGroup = posfield(property="modifierClass")


@posmodel
class RProductModifierModifierGroupInfo(RProductModifierGroupInfo):
    """
    R supports one-level expansion depth.
    Therefore, as a result of the request the field will be not an object but a string.
    """

    modifierClass: str = posfield(property="modifierclass")


@posmodel
class RProductModifierInfo(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    modifier: RProductModifier = posfield(property="modifier")
    # resource uri of R Product
    product: str = posfield(property="product")
    productModifierClass: RProductModifierModifierGroupInfo = posfield(property="product_modifier_class")
    defaultModifierQuantity: int = posfield(property="default_modifier_qty")


@posmodel
class RProductTaxGroup(POSModel):
    id: str = posfield(property="id", required=True, importFunc=lambda x: str(x))
    productGroup: RProductGroup = posfield(property="product_group")
    taxes: List[RProductTax] = posfield(property="taxes")


@posmodel
class RPrevailingTax(POSModel):
    taxRate: float = posfield(property="parameter_value", importFunc=lambda x: float(x))


@posmodel
class RProductAttribute(POSModel):
    """
    will be used for resources/AttributeValue and resources/Attribute
    they have the same structure
     {
            "active": true,
            "created_by": "/enterprise/User/5/",
            "created_date": "2018-11-14T15:20:37.799884",
            "establishment": "/enterprise/Establishment/1/",
            "id": 1,
            "name": "Type",
            "resource_uri": "/resources/Attribute/1/",
            "sort": 1,
            "updated_by": "/enterprise/User/5/",
            "updated_date": "2018-11-14T15:20:37.799947"
        },
    """

    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    # URI of Attribute object.
    resourceUri: str = posfield(property="resource_uri")


@posmodel
class RDiscount(POSModel):
    # URI of Establishment where this object was created
    establishment: str = posfield(property="establishment")
    # URI of an User API object which is responsible for this object creation
    createdBy: str = posfield(property="created_by")
    # URI of the user that last updated this object
    updatedBy: str = posfield(property="updated_by")
    # Barcode of the the discount
    barcode: str = posfield(property="barcode", maxLen=16)
    # Flag value specifying whether the discount is variable or not, 'true' if discount is variable.
    # That means that the amount of discount should be provided each time on POS.
    isVariable: bool = posfield(property="is_variable")
    # Flag value specifying whether this discount should be applied per item or not,
    # 'true' if discount applied per item
    discountAtItemLevel: bool = posfield(property="discount_at_item_level")
    # Amount of the discount (0 for Dynamic object)
    discountAmount: float = posfield(property="discount_amount")
    # Type: Amount = 0, Percent = 1
    discountType: int = posfield(property="discount_type")
    # Name of the discount (will be displayed in app)
    name: str = posfield(property="name")
    # 2 - per Order (also 0 - All and 1 - per Item)
    qualificationType: int = posfield(property="qualification_type")


@posmodel
class RServiceFee(POSModel):
    # URI of Establishment where this object was created
    establishment: str = posfield(property="establishment")
    # URI of an User API object which is responsible for this object creation
    createdBy: str = posfield(property="created_by")
    # URI of the user that last updated this object
    updatedBy: str = posfield(property="updated_by")
    # Rule amount used for calculation total money amount (0 for Dynamic object)
    amount: float = posfield(property="amount")
    # Flag which shows that we should use data from request, not from setting on backend. Used in Online Ordering
    dynamic: bool = posfield(property="dynamic")
    # Type: Item = 0, Order = 1
    applicationType: int = posfield(property="application_type")
    # Integer representing ServiceFee to be applied to subtotal of the order, or post tax or pre discount of the order.
    # 0 - FEE_APPLY_TOSUBTOTAL
    # 1 - FEE_APPLY_TO_POST_TAX
    # 2 - FEE_APPLY_TO_PRE_DISCOUNT
    applyTo: int = posfield(property="apply_to")
    # Minimum taxable amount
    minThreshold: float = posfield(property="min_threshold")
    # Name of ServiceFee (will be displayed in app)
    name: str = posfield(property="name")
    # Type: Amount = 0, Percent = 1
    serviceFeeType: int = posfield(property="servicefee_type")
    active: bool = posfield(property="active")
    alias: str = posfield(property="alias")
    # 1 - AUTOAPPLY_TIMESLOT
    # 2 - AUTOAPPLY_PAYMENTTYPE
    # 3 - AUTOAPPLY_GUESTCOUNT
    # 4 - AUTOAPPLY_DININGTYPE
    autoapplyType: int = posfield(property="autoapply_type")
    # autoapplyData Dict format depends on autoapplyType selection
    autoapplyData: Dict[str, Any] = posfield(property="autoapply_data")


@posmodel
class RWebOrderItemModifier(POSModel):
    modifierId: int = posfield(property="modifier")
    quantity: int = posfield(property="qty")
    price: float = posfield(property="modifier_price")


@posmodel
class RWebOrderItem(POSModel):
    modifierItems: List[RWebOrderItemModifier] = posfield(property="modifieritems")
    price: float = posfield(property="price")
    productId: int = posfield(property="product")
    quantity: int = posfield(property="quantity")
    # this is required for the kitchen
    specialRequest: str = posfield(property="special_request")
    productNameOverride: str = posfield(property="product_name_override")
    weight: int = posfield(property="weight")


@posmodel
class RWebOrderProductsSet(POSModel):
    id: int = posfield(property="id")
    products: List[RWebOrderItem] = posfield(property="products")


@posmodel
class RWebOrderItemWithUpsell(RWebOrderItem):
    hasUpsell: bool = posfield(property="has_upsell")
    productSets: List[RWebOrderProductsSet] = posfield(property="products_sets")


@posmodel
class RWebOrderComboItem(RWebOrderItem):
    isCombo: bool = posfield(property="is_combo")
    productSets: List[RWebOrderProductsSet] = posfield(property="products_sets")


@posmodel
class RWebOrderPaymentInfo(POSModel):
    amount: float = posfield(property="amount")
    paymentType: int = posfield(property="type")
    transactionId: str = posfield(property="transaction_id")
    tip: float = posfield(property="tip")


@posmodel
class RWebOrderCustomerAddress(POSModel):
    country: str = posfield(property="country")
    city: str = posfield(property="city")
    street1: str = posfield(property="street_1")
    street2: str = posfield(property="street_2")
    state: str = posfield(property="state")
    zipcode: str = posfield(property="zipcode")


@posmodel
class RWebOrderCustomer(POSModel):
    phone: str = posfield(property="phone")  # may not be empty!
    email: str = posfield(property="email")
    address: RWebOrderCustomerAddress = posfield(property="address")
    firstName: str = posfield(property="first_name")
    lastName: str = posfield(property="last_name")


@posmodel
class RTable(POSModel):
    id: int = posfield(property="id")
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    section: str = posfield(property="section")

    def toDeliverect(self) -> DeliverectFloor:
        """Returns an internal table representation of the current table."""
        return DeliverectFloor(id=str(self.id), name=self.name)


@posmodel
class RWebOrderInfo(POSModel):
    diningOptionId: int = posfield(property="dining_option")
    pickupTime: str = posfield(property="pickup_time")
    notes: str = posfield(property="notes")
    # this is required for the kitchen
    specialRequest: str = posfield(property="special_request")
    customer: RWebOrderCustomer = posfield(property="customer")
    callName: str = posfield(property="call_name")
    table: RTable = posfield(property="table")


@posmodel
class RWebOrderDiscount(POSModel):
    barcode: str = posfield(property="barcode")
    amount: float = posfield(property="amount")


@posmodel
class RWebOrderServiceFee(POSModel):
    alias: str = posfield(property="alias")
    amount: float = posfield(property="amount")


@posmodel
class RWebOrder(POSModel):
    establishmentId: int = posfield(property="establishment", required=True)
    items: List[RWebOrderItem] = posfield(property="items")
    paymentInfo: RWebOrderPaymentInfo = posfield(property="paymentInfo")
    orderInfo: RWebOrderInfo = posfield(property="orderInfo")
    discounts: List[RWebOrderDiscount] = posfield(property="discounts")
    serviceFees: List[RWebOrderServiceFee] = posfield(property="serviceFees")


@posmodel
class RComboItem(POSModel):
    # product uri
    resourceUri: str = posfield(property="product")


@posmodel
class RSlot(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    price: str = posfield(property="price")
    products_price: float = posfield(property="products_price")
    substitutions_price: float = posfield(property="substitutions_price")
    quantity: int = posfield(property="quantity")
    resourceUri: str = posfield(property="resource_uri")

    comboItemsSet: List[RComboItem] = posfield(property="combo_items")
    # TODO: add default logic later (auto select)
    defaultProducts: List[str] = posfield(property="default_products", default_factory=list)
    defaultProduct: str = posfield(property="default_product")


@posmodel
class RUpsell(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name", default="")
    price: float = posfield(property="price", importFunc=lambda x: float(x))
    resourceUri: str = posfield(property="resource_uri")
    slots: List[RSlot] = posfield(property="slots")


@posmodel
class RDynamicCombo(POSModel):
    id: int = posfield(property="id", required=True, importFunc=lambda x: str(x))
    active: bool = posfield(property="active")
    name: str = posfield(property="name")
    price: float = posfield(property="price", importFunc=lambda x: float(x))
    resourceUri: str = posfield(property="resource_uri")
    upsells: List[RUpsell] = posfield(property="upsells")


class RWebMenuProductModifierClassModifiers(BaseModel):
    sort: int
    price: int
    barcode: Optional[str]
    cost: str
    active: bool
    id: int
    modifier_class_id: int
    sku: Optional[str]
    name: str
    selected: bool
    is_quick: bool
    default_modifier_qty: int
    img_url: Optional[str]


class RWebMenuProductModifierClass(BaseModel):
    """modifier group"""

    sort: int
    maximum_amount: Optional[int]
    admin_modifier: bool
    active: bool
    id: int
    modifier_class_id: int
    forced: bool
    amount_free_is_dollars: Optional[str]
    name: str
    amount_free: int
    admin_mod_key: Optional[str]
    split: bool
    minimum_amount: Optional[int]
    modifiers: List[RWebMenuProductModifierClassModifiers] = Field(default_factory=list)


class RWebMenuProduct(BaseModel):
    sort: int
    id_category: int
    is_cold: bool
    description: Optional[str]
    modifier_classes: List[RWebMenuProductModifierClass] = Field(default_factory=list)
    sold_by_weight: bool
    attribute_type: int
    image: Optional[str]
    barcode: str
    stock_amount: int
    cost: float
    images: List[str]
    is_shipping: Optional[bool]
    id: int
    upcharge_price: int
    sku: Optional[str]
    is_gift: Optional[bool]
    name: str
    # timetables: List[str]
    is_combo: int  # todo bool
    has_upsell: bool
    max_price: Optional[int]
    # size_chart:
    # point_value: null,
    # course_number: null,
    # created_date: 06/08/2016 11:34,
    price: int
    uom: str


class RWebMenuCategory(BaseModel):
    sort: str
    parent_name: str
    # timetables: List[str]
    name: str
    products: List[RWebMenuProduct] = Field(default_factory=list)
    parent_id: int
    parent_sort: int
    image: Optional[str]
    id: int
    description: Optional[str]


class RWebMenu(BaseModel):
    # categories: List[str]
    categories: List[RWebMenuCategory] = Field(default_factory=list)
