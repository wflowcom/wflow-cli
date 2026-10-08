"""Generated from the wflow OpenAPI spec.

Regenerate with:

    uv run scripts/wflow_spec.py --models Document DocumentBase DocumentTypeFull DocumentEvent DocumentFile Comment Property PropertyDefinition ApprovalProcess

then review the diff. That command's dependency closure emits 31 classes, not the 21
below: the other 10 are schemas this codebase already models elsewhere, so delete them
from the regenerated output and import them instead of duplicating them —

- from wflow_api.models.account: DocumentTypeBase, Identity, TeamBase
- from wflow_api.models.registers: AddressType, KindRegister, Location, PaymentMethods,
  Register, Serie, VATReturnLine

Also delete `Property._value` from the regenerated output: the spec marks it
`writeOnly: true`, so wflow never sends it back and there is nothing here to read."""

from typing import Any

from pydantic import Field

from wflow_api.models.account import DocumentTypeBase, Identity, TeamBase
from wflow_api.models.common import WflowModel, WflowTimestamp
from wflow_api.models.registers import (
    AddressType,
    KindRegister,
    Location,
    PaymentMethods,
    Register,
    Serie,
    VATReturnLine,
)


class DocumentPayment(WflowModel):
    paidAmount: float | None = Field(default=None, description="Paid amount (decimal (18,2))")
    paidDate: WflowTimestamp | None = Field(default=None, description="Paid date (yyyy-mm-ddThh:mm:ss.ffffff)")
    paymentStatus: str | None = Field(default=None, description="One of: NotPaid, PartiallyPaid, Paid, OverPaid")
    paymentOrderAmount: float | None = Field(default=None, description="Payment order amount (decimal (18,2))")
    paymentOrderStatus: str | None = Field(default=None, description="One of: Requested, Created")
    activePaymentRequestDate: WflowTimestamp | None = Field(
        default=None, description="Active payment request date (yyyy-mm-ddThh:mm:ss.ffffff)"
    )


class DocumentBase(WflowModel):
    id: str | None = Field(default=None, description="Id")
    serie: Serie | None = None
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
    validFrom: WflowTimestamp | None = Field(default=None, description="Valid from (yyyy-mm-ddThh:mm:ss.ffffff)")
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
    taxExclusiveAmount: float | None = Field(default=None, description="Tax exclusive amount")
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
    partnerMainAddress: AddressType | None = None
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
    remainsToDeliverAmount: float | None = Field(default=None, description="Remains to deliver amount.")
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )
    expectedDeliveryDate: WflowTimestamp | None = Field(
        default=None, description="Expected delivery date - for orders only (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    accountCode: str | None = Field(default=None, description="Accounting account code")
    doNotPay: bool | None = Field(default=None, description="Do not pay")
    created: WflowTimestamp | None = Field(default=None, description="Creation date (yyyy-mm-ddThh:mm:ss.ffffff)")
    updated: WflowTimestamp | None = Field(default=None, description="Last update date (yyyy-mm-ddThh:mm:ss.ffffff)")
    lastAction: WflowTimestamp | None = Field(default=None, description="Last action date (yyyy-mm-ddThh:mm:ss.ffffff)")
    removed: WflowTimestamp | None = Field(default=None, description="Remove date (yyyy-mm-ddThh:mm:ss.ffffff)")
    locked: bool | None = Field(default=None, description="Locked attribute")
    approvalStatus: str | None = Field(
        default=None, description="One of: NotApproved, Approved, Rejected, Returned, None"
    )
    flowStatus: str | None = Field(
        default=None,
        description="One of: New, SendToExtractionWaiting, SendToExtractionError, SendToExtractionOK, Filled, Extracted, SentToReview, Reviewed, Sent, SendToERPWaiting, SendToERPError, SentToERP, PartlyDelivered, Delivered, NotConfirmed",
    )
    payment: DocumentPayment | None = None
    dataSource: str | None = Field(default=None, description="One of: ISDOC, ROSSUM, EKASA, API, WFLOWAI, ZUGFERD, UBL")
    source: str | None = Field(default=None, description="One of: Email, Api, MobileApp, WebApp, Rossum, Peppol")
    createdBy: str | None = Field(default=None, description="Name or login of user, who created the document")
    series: str | None = Field(default=None, description="Serie code - Deprecated")
    type: DocumentTypeBase | None = None
    tags: list[str] | None = Field(default=None, description="Array of tags added to the document")


class SequenceBase(WflowModel):
    id: str | None = None
    entity: str | None = None
    description: str | None = None
    fixedPart: str | None = None
    counter: str | None = None


class DocumentType(WflowModel):
    """Document type"""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    kind: str | None = Field(
        default=None,
        description="One of: IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, CustomerOrder, Other, Contract, IncomeCashReceipt",
    )
    default: bool | None = Field(default=None, description="Use as default attribute")
    erpExclude: bool | None = Field(default=None, description="Exclude from sending to ERP attribute")
    filesExtendName: bool | None = Field(default=None, description="Uploaded files from e-mail name extension")
    docCreatingMethod: str | None = Field(default=None, description="One of: Upload, Manually")
    autoStamp: str | None = Field(default=None, description="One of: None, New, Approved")
    serie: Serie | None = None
    sequence: SequenceBase | None = None
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )


class Partner(WflowModel):
    """Partner"""

    id: str | None = Field(default=None, description="Id")
    externalId: str | None = Field(default=None, description="External Id")
    ic: str | None = Field(default=None, description="Tax ID. (max 10 characters)")
    vat: str | None = Field(default=None, description="VAT ID.  (max 15 characters)")
    name: str | None = Field(default=None, description="Name")
    address: str | None = Field(default=None, description="Address (street, post code, town, country,...)")
    mainAddress: AddressType | None = None
    localVAT: str | None = Field(default=None, description="Local VAT ID")
    note: str | None = Field(default=None, description="Notes")
    phoneNo: str | None = Field(default=None, description="Phone No")
    mailAddress: str | None = Field(default=None, description="E-mail address")
    deliveryPeriod: int | None = Field(default=None, description="Standard delivery period in days")
    minOrderTotal: float | None = Field(default=None, description="Minimal order amount (decimal (18,2))")
    toleranceRate: int | None = Field(default=None, description="Automatic pairing tolerance threshold by total amount")
    language: str | None = Field(
        default=None, description="Primary language. ISO 639-1:2002 language code (2 characters)"
    )
    isValid: bool | None = Field(default=None, description="Validity attribute")
    businessRegisterRegistration: str | None = Field(default=None, description="Business register registration text")
    customer: bool | None = Field(default=None, description="Customer attribute")
    supplier: bool | None = Field(default=None, description="Supplier attribute")


class Accounting(WflowModel):
    """Accounting"""

    businessItemCode: str | None = Field(default=None, description="Business item code")
    accountingRule: KindRegister | None = None
    activity: Register | None = None
    businessCase: Register | None = None
    cardDocumentType: Register | None = None
    cashDocumentType: Register | None = None
    cashRegister: Register | None = None
    contraAccount: Register | None = None
    contract: Register | None = None
    costCenter: Register | None = None
    employee: Register | None = None
    paymentMethod: PaymentMethods | None = None
    project: Register | None = None
    vatControlStatementLine: Register | None = None
    vatReturnLine: VATReturnLine | None = None
    vatReverseChargeCode: Register | None = None
    vehicle: Register | None = None
    vatSupplyModeCode: str | None = Field(default=None, description="One of: Normal, TravelService, UsedGoods")
    vatApplyReductionCoefficient: bool | None = Field(
        default=None, description="VAT apply reduction coefficient indicator"
    )
    vatFixedAssets: bool | None = Field(default=None, description="VAT fixed assets indicator")
    vatMode: str | None = Field(
        default=None, description="One of: Standard, ReverseChargeDomestic, ReverseCharge, Excluded, InForeignCurrency"
    )


class DocumentVAT(WflowModel):
    """Document VAT"""

    rate: float | None = Field(default=None, description="VAT percent rate (decimal (4,2))")
    type: str | None = Field(default=None, description="One of: Exempt, FirstReduced, SecondReduced, Basic")
    base: float | None = Field(default=None, description="VAT base amount (decimal (18,2))")
    tax: float | None = Field(default=None, description="VAT tax amount (decimal (18,2))")


class IdentityBase(WflowModel):
    """Identity base"""

    login: str | None = Field(default=None, description="Login name.")
    firstName: str | None = Field(default=None, description="First name.")
    lastName: str | None = Field(default=None, description="Last name.")
    fullName: str | None = Field(default=None, description="Full name.")


class ApprovalProcessItem(WflowModel):
    """Approval process item"""

    level: int | None = Field(default=None, description="Level in approval process")
    team: TeamBase | None = None
    identity: IdentityBase | None = None
    date: WflowTimestamp | None = Field(default=None, description="Date of aproval result")
    status: str | None = Field(default=None, description="One of: NotApproved, Approved, Rejected, Returned, None")


class DocumentLine(WflowModel):
    """Document line"""

    id: str | None = Field(default=None, description="Total amount (decimal (18,2))")
    totalAmount: float | None = Field(default=None, description="Total amount (decimal (18,2))")
    totalAmountFC: float | None = Field(default=None, description="Total amonut in foriegn currency (decimal (18,2))")
    accountCode: str | None = Field(default=None, description="Accounting account code")
    currency: str | None = Field(default=None, description="Currency ISO code (fixed length 3 chars)")
    description: str | None = Field(default=None, description="Item description")
    quantity: float | None = Field(default=None, description="Quantity (decimal (14,6))")
    unitPrice: float | None = Field(default=None, description="Unit price (decimal (14,6))")
    measureUnit: str | None = Field(default=None, description="Measure unit")
    vatType: str | None = Field(default=None, description="One of: Exempt, FirstReduced, SecondReduced, Basic")
    vatRate: float | None = Field(default=None, description="VAT percent rate (decimal (4,2))")
    order: int | None = Field(default=None, description="Item order index in list")
    approval: ApprovalProcessItem | None = None
    changedAfterApprove: bool | None = Field(default=None, description="Changed after approve")
    accounting: Accounting | None = None
    code: str | None = Field(default=None, description="Item code (read only)")
    costCenter: Register | None = None
    contract: Register | None = None
    activity: Register | None = None


class Document(WflowModel):
    """Document"""

    id: str | None = Field(default=None, description="Id")
    serie: Serie | None = None
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
    validFrom: WflowTimestamp | None = Field(default=None, description="Valid from (yyyy-mm-ddThh:mm:ss.ffffff)")
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
    taxExclusiveAmount: float | None = Field(default=None, description="Tax exclusive amount")
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
    partnerMainAddress: AddressType | None = None
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
    remainsToDeliverAmount: float | None = Field(default=None, description="Remains to deliver amount.")
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )
    expectedDeliveryDate: WflowTimestamp | None = Field(
        default=None, description="Expected delivery date - for orders only (yyyy-mm-ddThh:mm:ss.ffffff)"
    )
    accountCode: str | None = Field(default=None, description="Accounting account code")
    doNotPay: bool | None = Field(default=None, description="Do not pay")
    created: WflowTimestamp | None = Field(default=None, description="Creation date (yyyy-mm-ddThh:mm:ss.ffffff)")
    updated: WflowTimestamp | None = Field(default=None, description="Last update date (yyyy-mm-ddThh:mm:ss.ffffff)")
    lastAction: WflowTimestamp | None = Field(default=None, description="Last action date (yyyy-mm-ddThh:mm:ss.ffffff)")
    removed: WflowTimestamp | None = Field(default=None, description="Remove date (yyyy-mm-ddThh:mm:ss.ffffff)")
    locked: bool | None = Field(default=None, description="Locked attribute")
    approvalStatus: str | None = Field(
        default=None, description="One of: NotApproved, Approved, Rejected, Returned, None"
    )
    flowStatus: str | None = Field(
        default=None,
        description="One of: New, SendToExtractionWaiting, SendToExtractionError, SendToExtractionOK, Filled, Extracted, SentToReview, Reviewed, Sent, SendToERPWaiting, SendToERPError, SentToERP, PartlyDelivered, Delivered, NotConfirmed",
    )
    payment: DocumentPayment | None = None
    dataSource: str | None = Field(default=None, description="One of: ISDOC, ROSSUM, EKASA, API, WFLOWAI, ZUGFERD, UBL")
    source: str | None = Field(default=None, description="One of: Email, Api, MobileApp, WebApp, Rossum, Peppol")
    createdBy: str | None = Field(default=None, description="Name or login of user, who created the document")
    series: str | None = Field(default=None, description="Serie code - Deprecated")
    type: DocumentType | None = None
    partner: Partner | None = None
    deliveryLocation: Location | None = None
    accounting: Accounting | None = None
    vaTs: list[DocumentVAT] | None = Field(default=None, description="VAT subtotals")
    lines: list[DocumentLine] | None = Field(default=None, description="Lines list")
    transactionId: str | None = Field(default=None, description="Transaction id")
    expenseCardId: str | None = Field(default=None, description="Card id")
    peppolMessageId: str | None = Field(
        default=None, description="Peppol message Id (PeppolIncomingEvent or PeppolOutgoingEvent Id)"
    )


class UserBase(WflowModel):
    """User base"""

    id: str | None = Field(default=None, description="Id")
    identity: Identity | None = None


class UserPermission(WflowModel):
    user: UserBase | None = None
    permission: str | None = Field(default=None, description="One of: All, OnlyAssigned, FullAccess")


class DocumentTypeFull(WflowModel):
    """Document type full"""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    kind: str | None = Field(
        default=None,
        description="One of: IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, CustomerOrder, Other, Contract, IncomeCashReceipt",
    )
    default: bool | None = Field(default=None, description="Use as default attribute")
    erpExclude: bool | None = Field(default=None, description="Exclude from sending to ERP attribute")
    filesExtendName: bool | None = Field(default=None, description="Uploaded files from e-mail name extension")
    docCreatingMethod: str | None = Field(default=None, description="One of: Upload, Manually")
    autoStamp: str | None = Field(default=None, description="One of: None, New, Approved")
    serie: Serie | None = None
    sequence: SequenceBase | None = None
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )
    users: list[UserPermission] | None = Field(default=None, description="Retrieves")


class DocumentEvent(WflowModel):
    id: str | None = None
    type: str | None = Field(
        default=None,
        description="One of: Create, Update, Delete, Restore, Approved, Unapproved, Locked, Unlocked, Rejected, Returned, FileAdded, FileDeleted, TaskAdded, TaskProcessed, SetDocumentRights, SetDocumentApprovals, DeleteDocumentApprovals, AddDocumentPayment, UpdateDocumentPayment, ChangeProperty, TimeStamped, Signed, AddDocumentPaymentRequest, Delivered, DeliverCanceled, SentByEmail, ReturnedBack, ChangedFlowStatus, ChangedKind, SentForSigning, Confirmed, Unconfirmed, SentFiles, AddDocumentPaymentOrder, DeleteDocumentPayment, DeleteDocumentPaymentRequest, MovedFromOrganization, Split, ChangeDocumentApprovals, Merged, Linked, SetAccess, ExpenseTransactionPaired, ExpenseTransactionUnpaired, SetMainFile, BudgetUpdated, MovedToOtherOrganization, MovedFromOtherOrganization",
    )
    identity: IdentityBase | None = None
    info: str | None = None
    created: WflowTimestamp | None = None


class DocumentFile(WflowModel):
    """Document attachment file"""

    id: str | None = Field(default=None, description="Id")
    name: str | None = Field(default=None, description="Name")
    main: bool | None = Field(default=None, description="Main attribute")
    created: WflowTimestamp | None = Field(default=None, description="Creation date (yyyy-mm-ddThh:mm:ss.ffffff)")
    signed: bool | None = Field(default=None, description="Whether the file is digitally signed")
    stamped: bool | None = Field(default=None, description="Whether the file is time-stamped")


class CommentTeam(WflowModel):
    id: str | None = Field(default=None, description="Id of CommentTeam")
    team: TeamBase | None = None
    isInTeam: bool | None = Field(default=None, description="Indicates whehter the user is in this Team")
    resolved: WflowTimestamp | None = Field(default=None, description="Date and Time of resolvment of the comment")
    resolver: IdentityBase | None = None


class Comment(WflowModel):
    """Comment"""

    id: str | None = Field(default=None, description="Id")
    author: IdentityBase | None = None
    text: str | None = Field(default=None, description="Text")
    created: WflowTimestamp | None = Field(default=None, description="Date of creation")
    updated: WflowTimestamp | None = Field(default=None, description="Last modified date")
    removed: WflowTimestamp | None = Field(default=None, description="Date of removal")
    nodes: str | None = Field(default=None, description="Nodes")
    markdown: str | None = Field(default=None, description="Markdown")
    teams: list[CommentTeam] | None = Field(default=None, description="List of teams")


class Property(WflowModel):
    """Custom property"""

    id: str | None = None
    name: str | None = Field(default=None, description="Name")
    order: int | None = Field(default=None, description="Order for presentation")
    show: bool | None = Field(default=None, description="Visibility indicator")
    type: str | None = None
    editable: bool | None = Field(default=None, description="Read/write indicator")
    kinds: list[str] | None = Field(
        default=None,
        description="Data One of: IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, CustomerOrder, Other, Contract, IncomeCashReceipt",
    )
    data: list[str] | None = None
    value: Any | None = Field(default=None, description="Value")

    def carries_definition(self) -> bool:
        return self.name is not None and self.type is not None


class PropertyDefinition(WflowModel):
    """Custom property definition"""

    id: str | None = None
    name: str | None = Field(default=None, description="Name")
    order: int | None = Field(default=None, description="Order for presentation")
    show: bool | None = Field(default=None, description="Visibility indicator")
    type: str | None = None
    editable: bool | None = Field(default=None, description="Read/write indicator")
    kinds: list[str] | None = Field(
        default=None,
        description="Data One of: IncomingInvoice, OutgoingInvoice, ExpenditureCashSlip, SupplierOrder, CustomerOrder, Other, Contract, IncomeCashReceipt",
    )
    data: list[str] | None = None


class ApprovalProcess(WflowModel):
    """Approval process"""

    pathName: str | None = Field(default=None, description="Path name")
    items: list[ApprovalProcessItem] | None = Field(default=None, description="Approval process item collection")
