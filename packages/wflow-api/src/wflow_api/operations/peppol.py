"""Peppol tag: the e-invoicing messages a workspace sends and receives over the Peppol network."""

import base64

from wflow_api.client import WflowClient
from wflow_api.errors import WflowError
from wflow_api.guards import path_segment, query_params
from wflow_api.models import OrgSlug, Page, Paged, PageSize, Query, Search, Sort
from wflow_api.models.common import FileContent
from wflow_api.models.peppol import Attachment, PeppolMessage, PeppolMessageDetail
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
