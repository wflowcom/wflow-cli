"""Register models, mirroring the schemas in the wflow OpenAPI spec.

These carry the spec's own schema names, including BusinessItemUpdateC and
PartnerPersonUpdateC, so the code and the published reference read side by side. The
register GET endpoints document no response body; every model here is the item schema
that the PUT on the same path documents.
"""

from pydantic import Field

from wflow_api.models.common import WflowModel


class Register(WflowModel):
    """The five fields every register shares."""

    id: str | None = None
    externalId: str | None = None
    code: str | None = None
    description: str | None = None
    isValid: bool | None = None


class RegisterBase(WflowModel):
    """A reference to a register record. The spec declares three fields; wflow sends five."""

    id: str | None = None
    externalId: str | None = None
    code: str | None = None
    description: str | None = None
    isValid: bool | None = None


class RegisterId(WflowModel):
    """A reference to a partner."""

    id: str | None = None
    externalId: str | None = None
    ic: str | None = Field(default=None, description="Company registration number")
    vat: str | None = Field(default=None, description="VAT identification number")
    name: str | None = None
    address: str | None = Field(default=None, description="Street, post code, town, country as one string")


# The spec gives this shape two names; RegisterId is the same fields.
NoCodeRegisterBase = RegisterId


class KindRegister(Register):
    kind: str | None = Field(
        default=None,
        description="IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, "
        "CustomerOrder, Contract, IncomeCashReceipt or Other",
    )


# The spec gives this shape two names; PaymentMethods is a KindRegister field for field.
PaymentMethods = KindRegister


class Serie(KindRegister):
    invoiceType: str | None = Field(
        default=None, description="TaxInvoice, CreditNote, DebitNote, Proforma or TaxInvoicePayment"
    )


class VATReturnLine(Register):
    reverseCharge: bool | None = None


class Location(Register):
    address: str | None = None
    contact: str | None = None


class AddressType(WflowModel):
    streetAndNumber: str | None = None
    addressSupplement: str | None = None
    postalCode: str | None = None
    city: str | None = None
    countryCode: str | None = Field(default=None, description="ISO two-letter country code")


class PartnerAccount(WflowModel):
    accountNo: str | None = None
    bankCode: str | None = None
    iban: str | None = None
    bic: str | None = Field(default=None, description="SWIFT code")
    currency: str | None = None


class PartnerPeppolId(WflowModel):
    peppolId: str | None = None
    isDefault: bool | None = None
    isValid: bool | None = None


class OrganizationPerson(WflowModel):
    id: str | None = None
    externalId: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    street: str | None = None
    postCode: str | None = None
    city: str | None = None
    phoneNo: str | None = None
    mailAddress: str | None = None
    language: str | None = Field(default=None, description="ISO 639-1 code")
    isValid: bool | None = None
    contractRole: str | None = Field(
        default=None, description="Sign, Stamp, Approve, SignWithBankId or SignWithCertificate"
    )


class PartnerPersonUpdateC(OrganizationPerson):
    partner: NoCodeRegisterBase | None = Field(default=None, description="The partner this person belongs to")


class PartnerFull(WflowModel):
    id: str | None = None
    externalId: str | None = None
    ic: str | None = Field(default=None, description="Company registration number")
    vat: str | None = Field(default=None, description="VAT identification number")
    name: str | None = None
    address: str | None = Field(default=None, description="Street, post code, town, country as one string")
    mainAddress: AddressType | None = None
    localVAT: str | None = None
    note: str | None = None
    phoneNo: str | None = None
    mailAddress: str | None = None
    deliveryPeriod: int | None = Field(default=None, description="Standard delivery period in days")
    minOrderTotal: float | None = None
    toleranceRate: int | None = Field(default=None, description="Automatic pairing tolerance by total amount")
    language: str | None = Field(default=None, description="ISO 639-1 code")
    isValid: bool | None = None
    businessRegisterRegistration: str | None = None
    customer: bool | None = None
    supplier: bool | None = None
    accountNo: str | None = None
    bankCode: str | None = None
    iban: str | None = None
    bic: str | None = None
    currency: str | None = None
    mainAccount: PartnerAccount | None = None
    accounts: list[PartnerAccount] | None = Field(default=None, description="Other bank accounts")
    peppolIds: list[PartnerPeppolId] | None = None


class BusinessItemUpdateC(WflowModel):
    """The spec declares no `updated`; wflow sends one on a read, so a PUT of that record carries it."""

    id: str | None = None
    externalId: str | None = None
    code: str | None = None
    description: str | None = None
    isValid: bool | None = None
    updated: str | None = Field(default=None, description="Last update date (yyyy-mm-ddThh:mm:ss.ffffff)")
    unitPrice: float | None = None
    vatType: str | None = Field(default=None, description="Exempt, FirstReduced, SecondReduced or Basic")
    currency: str | None = None
    purchase: bool | None = None
    sales: bool | None = None
    category: RegisterBase | None = None
    partner: RegisterId | None = None
    measureUnit: RegisterBase | None = None
