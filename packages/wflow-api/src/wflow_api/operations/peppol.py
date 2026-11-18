"""Peppol tag: the e-invoicing messages a workspace sends and receives over the Peppol network."""

import base64
from typing import Annotated

from pydantic import Field

from wflow_api.client import DOWNLOAD_TIMEOUT, WflowClient
from wflow_api.errors import WflowError
from wflow_api.guards import path_segment, query_params, write_json
from wflow_api.models import OrgSlug, Page, Paged, PageSize, Query, Search, Sort, WriteResult
from wflow_api.models.common import FileContent
from wflow_api.models.peppol import (
    Attachment,
    PeppolMessage,
    PeppolMessageDetail,
    PeppolMessageRejectRequest,
    SendDocumentViaPeppolRequest,
    SendDocumentViaPeppolRequestAttachment,
)
from wflow_api.operation import operation


@operation
async def list_peppol_messages(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[PeppolMessage]:
    """Peppol e-invoicing messages in the workspace, incoming and outgoing.

    Needs inbox access, and the workspace must have Peppol enabled.

    `query` and `sort` take these keys, in any letter case: `id`, `document.id`, `status`,
    `createdAt`, `documentType`, `senderId`, `receiverId`, `senderName`, `receiverName`,
    `statusChangedAt`, `message`, `direction`, `archivedAt`, `invoiceType`. Any other key
    fails the call. The values of `status`, `direction` and `documentType` are
    case-sensitive. Filter by document with `document.id`, not `documentId`. Archived
    messages are included; filter `archivedAt = null` to leave them out.

    `search` matches sender and receiver names, ignoring case and accents, and orders the
    results by relevance unless `sort` is given. A page holds 10 messages by default and
    at most 100.

    Fields:

    - `id` — pass to `get_peppol_message_detail` and `download_peppol_message_attachment`
    - `direction` — Incoming or Outgoing
    - `status` — Queued (in wflow's queue or handed to the Peppol provider), Sent,
      Delivered or Error; or an Invoice Response code: AP Accepted, RE Rejected,
      UQ Under query, CA Conditionally accepted, PD Paid. On an outgoing message the code
      is the counterparty's answer; on an incoming one it is the answer this workspace
      sent. AB and IP are not used.
    - `rejectReason`, `requiredAction` — meaningful only on incoming messages, where they
      record the rejection this workspace sent; on an outgoing message read `status` and
      `message` instead
    - `message` — the text of the last status event
    - `documentType` — the Peppol document type, e.g. Invoice or CreditNote
    - `senderId`, `senderName`, `receiverId`, `receiverName` — the Peppol participants
    - `peppolMessageId`, `peppolDocumentId` — the identifiers on the Peppol network
    - `document` — the linked wflow document: its `id`, `type` and `invoiceType`
      (TaxInvoice, CreditNote, DebitNote, Proforma or TaxInvoicePayment)
    - `createdAt`, `statusChangedAt` — when the message was created and its status last changed
    - `archivedAt` — when it was archived, or null while it is not
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/peppol/messages",
        params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[PeppolMessage].model_validate(payload or {})


@operation
async def get_peppol_message_detail(client: WflowClient, organization: OrgSlug, id: str) -> PeppolMessageDetail:
    """One Peppol message with the document it carries, its attachments and its transport metadata.

    Needs inbox access, and the workspace must have Peppol enabled. Get the id from
    `list_peppol_messages`. Only incoming messages carry a linked document and
    attachments: for an outgoing message the detail has no `document` and no
    `attachments`.

    Fields:

    - `message` — the message itself, with the fields `list_peppol_messages` documents
    - `document` — the wflow document made from the message, as `get_document` returns it
    - `attachments` — each with its `name` and `contentType`; pass the `name` to
      `download_peppol_message_attachment`
    - `metadata` — `documentIdentifier`, `documentFormat`, `processIdentifier` and `sentAt`
    """
    payload = await client.request("GET", f"/api/{organization}/peppol/messages/{path_segment(id)}/detail")
    return PeppolMessageDetail.model_validate(payload or {})


@operation
async def download_peppol_message_attachment(
    client: WflowClient, organization: OrgSlug, id: str, name: str, *, max_bytes: int | None = None
) -> FileContent:
    """Download one file of an incoming Peppol message, by its name.

    Needs inbox access, and the workspace must have Peppol enabled. The name
    `peppol-document.xml` is the Peppol document as it was received; the names of the
    other files are the `attachments[].name` values `get_peppol_message_detail` returns.
    Outgoing messages have no attachments, so every name is reported as not found for them.

    wflow sends the whole file, with no size cap. With `max_bytes` set, a larger file is
    refused rather than truncated.

    Fields:

    - `filename` — the attachment's name
    - `content_type` — MIME type, e.g. "application/xml"
    - `content` — the file's bytes
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/peppol/messages/{path_segment(id)}/attachment",
        params=query_params(name=name),
        timeout=DOWNLOAD_TIMEOUT,
    )
    attachment = Attachment.model_validate(payload or {})
    if attachment.content is None:
        raise WflowError(f"The attachment {name!r} came back with no content, so there is no file to return.")
    try:
        data = base64.b64decode(attachment.content, validate=True)
    except ValueError as error:
        raise WflowError(
            f"The attachment {name!r} came back with content that is not base64, so it cannot be decoded into a file."
        ) from error
    if max_bytes is not None and len(data) > max_bytes:
        raise WflowError(
            f"The attachment {name!r} is {len(data)} bytes, over the {max_bytes}-byte limit set for this download."
        )
    return FileContent(filename=attachment.name or name, content_type=attachment.contentType, content=data)


@operation
async def accept_peppol_message(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Accept an incoming Peppol message: send the Accepted (AP) response to its sender.

    For incoming messages only; get the id from `list_peppol_messages`. The response goes to
    the sender over the Peppol network, and the message's `status` changes to AP only once
    the Peppol provider confirms it, so read the message again to see the result. A sent
    response cannot be withdrawn. The same or another response may be sent later, but it
    follows this one rather than undoing it. The linked wflow document is not changed. Needs
    inbox access, and the workspace must have Peppol enabled.

    Fields: on the result —

    - `action` — "accepted"
    - `resource` — "peppol/messages"
    """
    await client.request("PUT", f"/api/{organization}/peppol/messages/{path_segment(id)}/accept")
    return WriteResult(action="accepted", resource="peppol/messages")


@operation
async def accept_peppol_message_conditionally(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Accept an incoming Peppol message on conditions: send the Conditionally accepted (CA) response.

    For incoming messages only; get the id from `list_peppol_messages`. The response goes to
    the sender over the Peppol network, and the message's `status` changes to CA only once
    the Peppol provider confirms it, so read the message again to see the result. A sent
    response cannot be withdrawn. The same or another response may be sent later, but it
    follows this one rather than undoing it. The linked wflow document is not changed. Needs
    inbox access, and the workspace must have Peppol enabled.

    Fields: on the result —

    - `action` — "conditionally accepted"
    - `resource` — "peppol/messages"
    """
    await client.request("PUT", f"/api/{organization}/peppol/messages/{path_segment(id)}/conditionallyaccept")
    return WriteResult(action="conditionally accepted", resource="peppol/messages")


@operation
async def mark_peppol_message_under_query(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Put an incoming Peppol message under query: send the Under query (UQ) response to its sender.

    For incoming messages only; get the id from `list_peppol_messages`. The response goes to
    the sender over the Peppol network, and the message's `status` changes to UQ only once
    the Peppol provider confirms it, so read the message again to see the result. A sent
    response cannot be withdrawn. The same or another response may be sent later, but it
    follows this one rather than undoing it. The linked wflow document is not changed. Needs
    inbox access, and the workspace must have Peppol enabled.

    Fields: on the result —

    - `action` — "marked under query"
    - `resource` — "peppol/messages"
    """
    await client.request("PUT", f"/api/{organization}/peppol/messages/{path_segment(id)}/underquery")
    return WriteResult(action="marked under query", resource="peppol/messages")


@operation
async def mark_peppol_message_paid(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Mark an incoming Peppol message paid: send the Paid (PD) response to its sender.

    For incoming messages only; get the id from `list_peppol_messages`. The response goes to
    the sender over the Peppol network, and the message's `status` changes to PD only once
    the Peppol provider confirms it, so read the message again to see the result. A sent
    response cannot be withdrawn. The same or another response may be sent later, but it
    follows this one rather than undoing it. The linked wflow document is not changed and
    records no payment. Needs inbox access, and the workspace must have Peppol enabled.

    Fields: on the result —

    - `action` — "marked paid"
    - `resource` — "peppol/messages"
    """
    await client.request("PUT", f"/api/{organization}/peppol/messages/{path_segment(id)}/paid")
    return WriteResult(action="marked paid", resource="peppol/messages")


@operation
async def reject_peppol_message(
    client: WflowClient,
    organization: OrgSlug,
    id: str,
    reason: Annotated[
        str | None,
        Field(
            default=None,
            description="One of: NoIssue, ReferencesIncorrect, LegalInformationIncorrect, ReceiverUnknown, "
            "ItemQualityInsufficient, DeliveryIssues, PricesIncorrect, QuantityIncorrect, ItemsIncorrect, "
            "PaymentTermsIncorrect, NotRecognized, FinanceIncorrect, PartiallyPaid, Other. Omitted means NoIssue",
        ),
    ] = None,
    requiredAction: Annotated[
        str | None,
        Field(
            default=None,
            description="One of: NoActionRequired, ProvideInformation, IssueNewInvoice, CreditFully, "
            "CreditPartially, CreditTheAmount, Other. Omitted means NoActionRequired. Stored on the message "
            "but never sent to the counterparty",
        ),
    ] = None,
    note: Annotated[
        str | None,
        Field(default=None, description="Text sent to the counterparty with the rejection"),
    ] = None,
) -> WriteResult:
    """Reject an incoming Peppol message: send the Rejected (RE) response to its sender.

    For incoming messages only; get the id from `list_peppol_messages`. The response goes to
    the sender over the Peppol network, and the message's `status` changes to RE only once
    the Peppol provider confirms it, so read the message again to see the result. A sent
    response cannot be withdrawn. The same or another response may be sent later, but it
    follows this one rather than undoing it. The linked wflow document is not changed. Needs
    the right to reject Peppol messages; inbox access alone is not enough. The workspace
    must have Peppol enabled.

    Every argument after `id` is optional. `reason` is sent to the counterparty; without it
    the rejection says there is no issue (NoIssue). `note` is sent with it and is stored as
    the message's `message` text. `requiredAction` is stored on the message as
    `requiredAction`, defaulting to NoActionRequired, but it is never sent: the counterparty
    does not see it, so put what they must do in `note`.

    Fields: on the result —

    - `action` — "rejected"
    - `resource` — "peppol/messages"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/peppol/messages/{path_segment(id)}/reject",
        json=write_json(PeppolMessageRejectRequest(reason=reason, requiredAction=requiredAction, note=note)),
    )
    return WriteResult(action="rejected", resource="peppol/messages")


@operation
async def send_document_via_peppol(
    client: WflowClient,
    organization: OrgSlug,
    documentId: str,
    recipientPeppolId: Annotated[
        str,
        Field(
            min_length=1,
            description='The recipient\'s Peppol id as scheme:value, e.g. "9915:cz12345678"; the '
            "iso6523-actorid-upis:: prefix is also accepted",
        ),
    ],
    note: Annotated[
        str | None,
        Field(default=None, description="Text sent to the recipient, joined with the document's description"),
    ] = None,
    attachments: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Ids of the document's own files, from list_document_files, to send with it. The "
            "main file is sent only if its id is listed",
        ),
    ] = None,
) -> WriteResult:
    """Send an outgoing invoice to its recipient over the Peppol network.

    Only `OutgoingInvoice` documents can be sent. The document needs a partner name, and the
    workspace needs a Peppol connection with its own Peppol id. `recipientPeppolId` is
    required: wflow does not take it from the document's partner. Needs the right to manage
    documents, and the workspace must have Peppol enabled.

    wflow generates a UBL Invoice from the document's data, or a UBL CreditNote when the
    document's `invoiceType` is CreditNote. The document's main file or PDF is not sent
    unless its id is in `attachments`; attachments are the document's own file ids from
    `list_document_files`. `note` goes to the recipient, joined with the document's
    description.

    Sending locks the document, records a "sent via Peppol" event on it and runs the
    workspace's automations; the document's flow status becomes Sent later. A second send of
    the same document is refused unless every earlier outgoing message for it ended in Error
    or RE. When the document fails Peppol validation, the failures come back grouped by
    rule. Follow the delivery with `list_peppol_messages` and the `query`
    `document.id = "<id>"`.

    Fields: on the result —

    - `action` — "queued"
    - `resource` — "documents/peppol"
    """
    body = SendDocumentViaPeppolRequest(
        recipientPeppolId=recipientPeppolId,
        note=note,
        attachments=None
        if attachments is None
        else [SendDocumentViaPeppolRequestAttachment(fileId=i) for i in attachments],
    )
    await client.request(
        "POST",
        f"/api/{organization}/documents/{path_segment(documentId)}/peppol/send",
        json=write_json(body),
    )
    return WriteResult(action="queued", resource="documents/peppol")
