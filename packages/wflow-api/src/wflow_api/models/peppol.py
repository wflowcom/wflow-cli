"""Generated from the wflow OpenAPI spec.

Regenerate with:

    uv run scripts/wflow_spec.py --models PeppolMessageDetail PeppolMessageRejectRequest SendDocumentViaPeppolRequest

then review the diff. That command's dependency closure emits 28 classes, not the 8
below: the other 20 are `Document`, `DocumentTypeBase` and the schemas `Document`
depends on, which this codebase already models elsewhere, so delete them from the
regenerated output and import them instead of duplicating them —

- from wflow_api.models.account: DocumentTypeBase
- from wflow_api.models.documents: Document

Also replace every `datetime` with `WflowTimestamp`, and keep the note on
`PeppolMessage.status` that AB and IP are not used."""

from pydantic import Field

from wflow_api.models.account import DocumentTypeBase
from wflow_api.models.common import WflowModel, WflowTimestamp
from wflow_api.models.documents import Document


class DocumentLink(WflowModel):
    """Represents a lightweight reference to a linked document."""

    id: str | None = Field(default=None, description="Gets or sets the internal document ID.")
    type: DocumentTypeBase | None = None
    invoiceType: str | None = Field(
        default=None, description="One of: TaxInvoice, CreditNote, DebitNote, Proforma, TaxInvoicePayment"
    )


class PeppolMessage(WflowModel):
    """Represents a PEPPOL message with sender/receiver and document metadata."""

    id: str | None = Field(default=None, description="Gets or sets the internal message ID.")
    peppolMessageId: str | None = Field(default=None, description="Gets or sets the external PEPPOL message ID.")
    peppolDocumentId: str | None = Field(default=None, description="Gets or sets the PEPPOL document ID.")
    status: str | None = Field(
        default=None,
        description="One of: Queued, Sent, Delivered, Error, AB, IP, AP, PD, RE, CA, UQ. AB and IP are not used.",
    )
    statusChangedAt: WflowTimestamp | None = Field(
        default=None, description="Gets or sets the date and time when status was last changed."
    )
    rejectReason: str | None = Field(
        default=None,
        description="One of: NoIssue, ReferencesIncorrect, LegalInformationIncorrect, ReceiverUnknown, ItemQualityInsufficient, DeliveryIssues, PricesIncorrect, QuantityIncorrect, ItemsIncorrect, PaymentTermsIncorrect, NotRecognized, FinanceIncorrect, PartiallyPaid, Other",
    )
    requiredAction: str | None = Field(
        default=None,
        description="One of: NoActionRequired, ProvideInformation, IssueNewInvoice, CreditFully, CreditPartially, CreditTheAmount, Other",
    )
    createdAt: WflowTimestamp | None = Field(
        default=None, description="Gets or sets the date and time when the message was created."
    )
    documentType: str | None = Field(
        default=None,
        description="One of: ApplicationResponse, AttachedDocument, AwardedNotification, BillOfLading, CallForTenders, Catalogue, CatalogueDeletion, CatalogueItemSpecificationUpdate, CataloguePricingUpdate, CatalogueRequest, CertificateOfOrigin, ContractAwardNotice, ContractNotice, CreditNote, DebitNote, DespatchAdvice, DocumentStatus, DocumentStatusRequest, ExceptionCriteria, ExceptionNotification, Forecast, ForecastRevision, ForwardingInstructions, FreightInvoice, FulfilmentCancellation, GoodsItemItinerary, GuaranteeCertificate, InstructionForReturns, InventoryReport, Invoice, ItemInformationRequest, Order, OrderCancellation, OrderChange, OrderResponse, OrderResponseSimple, PackingList, PriorInformationNotice, ProductActivity, Quotation, ReceiptAdvice, Reminder, RemittanceAdvice, RequestForQuotation, RetailEvent, SelfBilledCreditNote, SelfBilledInvoice, Statement, StockAvailabilityReport, Tender, TenderReceipt, TendererQualification, TendererQualificationResponse, TradeItemLocationProfile, TransportExecutionPlan, TransportExecutionPlanRequest, TransportProgressStatus, TransportProgressStatusRequest, TransportServiceDescription, TransportServiceDescriptionRequest, TransportationStatus, TransportationStatusRequest, UnawardedNotification, UtilityStatement, Waybill",
    )
    senderId: str | None = Field(default=None, description="Gets or sets the sender PEPPOL participant ID.")
    senderName: str | None = Field(default=None, description="Gets or sets the sender display name.")
    receiverId: str | None = Field(default=None, description="Gets or sets the receiver PEPPOL participant ID.")
    receiverName: str | None = Field(default=None, description="Gets or sets the receiver display name.")
    message: str | None = Field(default=None, description="Gets or sets the human-readable message text.")
    document: DocumentLink | None = None
    archivedAt: WflowTimestamp | None = Field(
        default=None, description="Gets or sets the date and time when the message was archived."
    )
    direction: str | None = Field(default=None, description="One of: Incoming, Outgoing")


class Attachment(WflowModel):
    """Represents a PEPPOL message attachment."""

    content: str | None = Field(default=None, description="Gets or sets the attachment content.")
    contentType: str | None = Field(default=None, description="Gets or sets the MIME content type.")
    name: str | None = Field(default=None, description="Gets or sets the attachment file name.")


class MessageMetadata(WflowModel):
    documentIdentifier: str | None = None
    documentFormat: str | None = None
    sentAt: WflowTimestamp | None = None
    processIdentifier: str | None = None


class PeppolMessageDetail(WflowModel):
    """Represents detailed PEPPOL message data including document content and metadata."""

    message: PeppolMessage | None = None
    document: Document | None = None
    attachments: list[Attachment] | None = Field(
        default=None, description="Gets or sets the list of document attachments."
    )
    metadata: MessageMetadata | None = None


class PeppolMessageRejectRequest(WflowModel):
    """Represents a request to reject a PEPPOL message."""

    reason: str | None = Field(
        default=None,
        description="One of: NoIssue, ReferencesIncorrect, LegalInformationIncorrect, ReceiverUnknown, ItemQualityInsufficient, DeliveryIssues, PricesIncorrect, QuantityIncorrect, ItemsIncorrect, PaymentTermsIncorrect, NotRecognized, FinanceIncorrect, PartiallyPaid, Other",
    )
    requiredAction: str | None = Field(
        default=None,
        description="One of: NoActionRequired, ProvideInformation, IssueNewInvoice, CreditFully, CreditPartially, CreditTheAmount, Other",
    )
    note: str | None = Field(default=None, description="Gets or sets an optional note with additional details.")


class SendDocumentViaPeppolRequestAttachment(WflowModel):
    fileId: str | None = None


class SendDocumentViaPeppolRequest(WflowModel):
    recipientPeppolId: str | None = None
    note: str | None = None
    attachments: list[SendDocumentViaPeppolRequestAttachment] | None = None
