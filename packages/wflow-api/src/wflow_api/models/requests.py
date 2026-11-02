"""Request bodies for the write endpoints, generated from the wflow OpenAPI spec.

Regenerate with:

    uv run scripts/wflow_spec.py --models DocumentUpdate DocumentTypeFull PropertyUpdate PropertyDefinition PaymentCreate IdType RoleUpdate TeamUpdate UserUpdate StorageFolderUpdate WebHookRegistration ApprovalsTemplateUpdate ApprovalsTemplateTeams StructuredFilter ApiClientResult

then review the diff; hand-written descriptions live here and must not be lost.

Every field is optional, and operations serialise with `model_dump(exclude_none=True)`: a whole-record
write that sent every unset optional as null would clear data the caller never mentioned.

That command's dependency closure emits 32 classes, not the 23 below. The other 9 are schemas
this codebase already models elsewhere, so delete them from the regenerated output — one name
must mean one shape. Four are imported back, so that every write body is reachable from here:

- from wflow_api.models.admin: ApprovalsTemplatesTeam, WebHookRegistration
- from wflow_api.models.documents: DocumentTypeFull, PropertyDefinition

The remaining five — `Identity`, `SequenceBase`, `UserBase` and `UserPermission` from
wflow_api.models.documents, `Serie` from wflow_api.models.registers — reach the closure only as
dependencies of DocumentTypeFull. With that imported, nothing here needs them: drop them."""

from typing import Any

from pydantic import Field

from wflow_api.models.admin import ApprovalsTemplatesTeam, WebHookRegistration  # noqa: F401 — re-exported
from wflow_api.models.common import WflowModel, WflowTimestamp
from wflow_api.models.documents import DocumentTypeFull, PropertyDefinition  # noqa: F401 — re-exported


class DocumentUpdateType(WflowModel):
    """Document update model"""

    id: str | None = Field(default=None, description="Id")
    kind: str | None = Field(
        default=None,
        description="One of: IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, CustomerOrder, Other, Contract, IncomeCashReceipt",
    )


class DocumentUpdateAddressType(WflowModel):
    """Document update address type with individual property change tracking"""

    streetAndNumber: str | None = Field(default=None, description="Street and number")
    addressSupplement: str | None = Field(default=None, description="Address supplement (additional address info)")
    postalCode: str | None = Field(default=None, description="Postal code")
    city: str | None = Field(default=None, description="City")
    countryCode: str | None = Field(default=None, description="Country code (ISO 3166-1 alpha-2)")


class DocumentUpdateRegister(WflowModel):
    """Document update register"""

    id: str | None = Field(default=None, description="Id")
    externalId: str | None = Field(default=None, description="External Id")
    code: str | None = Field(default=None, description="Code")


class DocumentUpdatePartner(WflowModel):
    """Document update model"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")


class DocumentUpdateVat(WflowModel):
    """Document update VAT"""

    type: str | None = Field(default=None, description="One of: Exempt, FirstReduced, SecondReduced, Basic")
    rate: float | None = Field(default=None, description="VAT percent rate (decimal (4,2))")
    base: float | None = Field(default=None, description="VAT base amount (decimal (18,2))")
    tax: float | None = Field(default=None, description="VAT tax amount (decimal (18,2))")


class DocumentUpdateAccounting(WflowModel):
    """Document for update accounting"""

    businessItemCode: str | None = Field(default=None, description="Business item code")
    accountingRule: DocumentUpdateRegister | None = None
    activity: DocumentUpdateRegister | None = None
    businessCase: DocumentUpdateRegister | None = None
    cardDocumentType: DocumentUpdateRegister | None = None
    cashDocumentType: DocumentUpdateRegister | None = None
    cashRegister: DocumentUpdateRegister | None = None
    contraAccount: DocumentUpdateRegister | None = None
    contract: DocumentUpdateRegister | None = None
    costCenter: DocumentUpdateRegister | None = None
    employee: DocumentUpdateRegister | None = None
    paymentMethod: DocumentUpdateRegister | None = None
    project: DocumentUpdateRegister | None = None
    vatControlStatementLine: DocumentUpdateRegister | None = None
    vatReturnLine: DocumentUpdateRegister | None = None
    vatReverseChargeCode: DocumentUpdateRegister | None = None
    vehicle: DocumentUpdateRegister | None = None
    vatSupplyModeCode: str | None = Field(default=None, description="One of: Normal, TravelService, UsedGoods")
    vatApplyReductionCoefficient: bool | None = Field(
        default=None, description="VAT apply reduction coefficient indicator"
    )
    vatFixedAssets: bool | None = Field(default=None, description="VAT fixed assets indicator")
    vatMode: str | None = Field(
        default=None, description="One of: Standard, ReverseChargeDomestic, ReverseCharge, Excluded, InForeignCurrency"
    )


class DocumentUpdateLine(WflowModel):
    """Document update line"""

    id: str | None = Field(default=None, description="Id")
    totalAmount: float | None = Field(default=None, description="Total amount (decimal (18,2))")
    totalAmountFC: float | None = Field(default=None, description="Total amonut in foriegn currency (decimal (18,2))")
    accountCode: str | None = Field(default=None, description="Accounting account code")
    currency: str | None = Field(default=None, description="Currency ISO code (fixed length 3 chars)")
    description: str | None = Field(default=None, description="Item description")
    quantity: float | None = Field(default=None, description="Quantity (decimal (14,6))")
    unitPrice: float | None = Field(default=None, description="Unit price (decimal (14,6))")
    measureUnit: str | None = Field(default=None, description="Measure unit")
    order: int | None = Field(default=None, description="Item order index in list")
    accounting: DocumentUpdateAccounting | None = None
    vatType: str | None = Field(default=None, description="One of: Exempt, FirstReduced, SecondReduced, Basic")
    vatRate: float | None = Field(default=None, description="VAT percent rate (decimal (4,2))")
    code: str | None = Field(default=None, description="Item code")
    costCenter: DocumentUpdateRegister | None = None
    contract: DocumentUpdateRegister | None = None
    activity: DocumentUpdateRegister | None = None


class DocumentUpdate(WflowModel):
    """Document for update"""

    id: str | None = Field(default=None, description="Id")
    type: DocumentUpdateType | None = None
    number: str | None = Field(default=None, description="Number")
    internalCode: str | None = Field(default=None, description="Internal code")
    vatDocumentCode: str | None = Field(default=None, description="VAT code")
    variableSymbol: str | None = Field(default=None, description="Variable symbol")
    constantSymbol: str | None = Field(default=None, description="Constant symbol")
    specificSymbol: str | None = Field(default=None, description="Specific symbol")
    issueDate: WflowTimestamp | None = Field(default=None, description="Issue date (yyyy-mm-ddThh:mm:ss.ffffff)")
    dueDate: WflowTimestamp | None = Field(default=None, description="Due date (yyyy-mm-ddThh:mm:ss.ffffff)")
    vatDate: WflowTimestamp | None = Field(default=None, description="VAT date (yyyy-mm-ddThh:mm:ss.ffffff)")
    acceptDate: WflowTimestamp | None = Field(default=None, description="Accept date (yyyy-mm-ddThh:mm:ss.ffffff)")
    caseDate: WflowTimestamp | None = Field(default=None, description="Case date (yyyy-mm-ddThh:mm:ss.ffffff)")
    validFrom: WflowTimestamp | None = Field(
        default=None, description="Valid from (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    validTo: WflowTimestamp | None = Field(
        default=None, description="Valid to (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    effectiveFrom: WflowTimestamp | None = Field(
        default=None, description="Effective from (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    effectiveTo: WflowTimestamp | None = Field(
        default=None, description="Effective to (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    signatureDate: WflowTimestamp | None = Field(
        default=None, description="Signature date (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    reviewDate: WflowTimestamp | None = Field(
        default=None, description="Review date (Contract kind) (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    accountTerm: str | None = Field(default=None, description="Accounting period (yyyy/mm)")
    vatTerm: str | None = Field(default=None, description="VAT period (yyyy/mm)")
    totalAmount: float | None = Field(default=None, description="Total amount (decimal (18,2))")
    roundingAmount: float | None = Field(default=None, description="Rounding ammount (decimal (3,2))")
    totalAmountFC: float | None = Field(default=None, description="Total amonut in foriegn currency (decimal (18,2))")
    advanceAmount: float | None = Field(default=None, description="Advance amount (decimal (18,2))")
    currency: str | None = Field(default=None, description="Currency ISO code (fixed length 3 chars)")
    partnerIC: str | None = Field(default=None, description="Partner ID")
    partnerVAT: str | None = Field(default=None, description="Partner VAT ID")
    partnerLocalVAT: str | None = Field(default=None, description="Partner local VAT ID")
    partnerName: str | None = Field(default=None, description="Partner name")
    partnerAddress: str | None = Field(
        default=None, description="Partner address (street, post code, town, country,...)"
    )
    partnerMainAddress: DocumentUpdateAddressType | None = None
    partnerEmail: str | None = Field(default=None, description="Partner e-mail address")
    accountNo: str | None = Field(default=None, description="Partner bank account No")
    bankCode: str | None = Field(default=None, description="Partner bank code")
    iban: str | None = Field(default=None, description="Partner IBAN")
    bic: str | None = Field(default=None, description="Partner BIC code (SWIFT)")
    meIC: str | None = Field(default=None, description="Recipient's ID")
    meVAT: str | None = Field(default=None, description="Recipient's VAT")
    myBankAccountNo: str | None = Field(
        default=None, description="Recipient's bank account number (snapshot taken at document creation)"
    )
    myBankCode: str | None = Field(
        default=None, description="Recipient's bank code (snapshot taken at document creation)"
    )
    myIBAN: str | None = Field(default=None, description="Recipient's IBAN (snapshot taken at document creation)")
    myBIC: str | None = Field(default=None, description="Recipient's BIC/SWIFT (snapshot taken at document creation)")
    myBankCurrency: str | None = Field(
        default=None, description="Recipient's bank account currency (snapshot taken at document creation)"
    )
    exchangeRate: float | None = Field(default=None, description="Exchange rate")
    exchangeRateUnits: int | None = Field(default=None, description="Exchange rate units")
    tag: str | None = Field(default=None, description="Special document identification")
    orderNo: str | None = Field(default=None, description="Linked order number")
    description: str | None = Field(default=None, description="Document description")
    contactPersonName: str | None = Field(default=None, description="Contact person name")
    contactPersonEmail: str | None = Field(default=None, description="Contact person email")
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )
    expectedDeliveryDate: WflowTimestamp | None = Field(
        default=None, description="Expected delivery date - for orders only (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    deliveryLocation: DocumentUpdateRegister | None = None
    series: str | None = Field(default=None, description="Series")
    depricatedSeries: bool | None = None
    serie: DocumentUpdateRegister | None = None
    accountCode: str | None = Field(default=None, description="Accounting account code")
    doNotPay: bool | None = Field(default=None, description="Do not pay")
    partner: DocumentUpdatePartner | None = None
    vaTs: list[DocumentUpdateVat] | None = Field(default=None, description="VAT subtotals")
    lines: list[DocumentUpdateLine] | None = Field(default=None, description="Lines list")
    accounting: DocumentUpdateAccounting | None = None
    taxExclusiveAmount: float | None = None
    taxAmount: float | None = None


class PropertyUpdate(WflowModel):
    """Custom property for update"""

    id: str | None = Field(default=None, description="Id")
    value: Any | None = Field(default=None, description="Value")


class PaymentCreate(WflowModel):
    date: WflowTimestamp | None = None
    info: str | None = None
    amount: float | None = None


class IdType(WflowModel):
    id: str | None = None


class RoleUpdate(WflowModel):
    """Role for update"""

    name: str | None = Field(default=None, description="Gets or sets the name.")
    description: str | None = Field(default=None, description="Gets or sets the description.")
    users: list[str] | None = Field(default=None, description="Gets or sets the users collection.")
    rights: list[str] | None = Field(
        default=None,
        description="Gets or sets the rights collection. One of: CanApprove, CanReview, CanManageApprovalPath, CanCreateDocument, CanDeleteDocument, CanManageAccess, CanChangeDocumentType, CanLock, CanManageAttachments, CanSendToExtraction, CanSendToReview, CanSendToErp, CanManageDocumentLinks, CanManageDocument, CanManageDocumentAccounting, CanManageCustomProperty, CanManageTags, CanManagePayments, CanMarkForPayment, CanExport, CanManageExternalSignature, CanStamp, CanManagePartners, CanManageBusinessItems, CanManageDocumentLinesTemplates, CanManageRegisters, CanManageSettings, CanManageFileStorage, CanManageExpenses, CanViewExpenses, CanViewReporting, CanManageBudgeting, CanManageDocumentBudgets, CanMoveDocumentToOtherOrganization, CanAccessInbox, CanRejectPeppolMessage",
    )


class TeamUpdate(WflowModel):
    """Team for updating"""

    name: str | None = Field(default=None, description="Gets or sets the name.")
    description: str | None = Field(default=None, description="Gets or sets the description.")
    users: list[str] | None = Field(default=None, description="Gets or sets the users collection.")


class IdAndPermission(WflowModel):
    id: str | None = None
    permission: str | None = Field(default=None, description="One of: All, OnlyAssigned, FullAccess")


class UserUpdate(WflowModel):
    """User to update"""

    login: str | None = Field(default=None, description="Login name.")
    hasFullAccess: bool | None = Field(default=None, description="Has full access permission.")
    roles: list[IdType] | None = Field(default=None, description="Role membership.")
    teams: list[IdType] | None = Field(default=None, description="Team membership.")
    documentTypes: list[IdAndPermission] | None = Field(default=None, description="Document Type access")


class StorageFolderUpdate(WflowModel):
    """Storage folder for udate"""

    id: str | None = Field(default=None, description="Gets or sets the identifier.")
    parentId: str | None = Field(default=None, description="Gets or sets the parent identifier.")
    name: str | None = Field(default=None, description="Gets or sets the name.")


class ApprovalsTemplateUpdate(WflowModel):
    """Approvals template for update"""

    teams: list[ApprovalsTemplatesTeam] | None = Field(default=None, description="Approvals teams collection")
    accessTeams: list[str] | None = Field(default=None, description="Teams collection for automatic set access")
    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    conditionFolders: list[str] | None = Field(
        default=None, description="Storage folder IDs collection for conditional assignment"
    )
    validationLockLevel: int | None = Field(default=None, description="Validation lock level")


class ApprovalsTemplateTeams(WflowModel):
    """Approvals template teams for update"""

    teams: list[ApprovalsTemplatesTeam] | None = Field(default=None, description="Approvals teams collection")
    accessTeams: list[str] | None = Field(default=None, description="Teams collection for automatic set access")


class Filter(WflowModel):
    operator: str | None = Field(default=None, description="One of: EQ, NE, GT, GE, LT, LE, IN, NI, CO, NC, DR, FD")
    value: Any | None = None


class ColumnAndFilter(WflowModel):
    column: str | None = None
    filters: list[Filter] | None = None


class PropertyFilter(WflowModel):
    operator: str | None = Field(default=None, description="One of: EQ, NE, GT, GE, LT, LE, IN, NI, CO, NC, DR, FD")
    value: Any | None = None
    key: str | None = None


class StructuredFilter(WflowModel):
    search: str | None = None
    sort: str | None = None
    filters: list[ColumnAndFilter] | None = None
    propertyFilters: list[PropertyFilter] | None = None
    validationType: list[str] | None = Field(
        default=None,
        description="One of: Duplicity, UnreliablePayer, RequiredField, InconsistentAmountsTotal, InconsistentAmountsLines, VatCalculation, VatRate, ExtremeDate, InvalidOrganization, InconsistentLines, MissingPartner, PartnerBankAccountMismatch, IbanValidation",
    )

    def with_empty_restrictions(self) -> "StructuredFilter":
        """The export endpoint answers 500 to a null `search`, `filters` or `propertyFilters`;
        sent empty, each one restricts nothing, which is what leaving it out means."""
        return self.model_copy(
            update={
                "search": self.search if self.search is not None else "",
                "filters": self.filters if self.filters is not None else [],
                "propertyFilters": self.propertyFilters if self.propertyFilters is not None else [],
            }
        )


class ApiClientResult(WflowModel):
    id: str | None = None
    secret: str | None = None
