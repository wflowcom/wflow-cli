"""Documents tag: the documents themselves, and everything hanging off one."""

import json
from typing import Annotated, Any

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import ensure_list, path_segment, query_params, write_json, write_json_list
from wflow_api.models import (
    DocumentUpdate,
    OrgSlug,
    Page,
    Paged,
    PageSize,
    PaymentCreate,
    Query,
    Search,
    Sort,
    StructuredFilter,
    TeamBase,
    WriteResult,
)
from wflow_api.models.common import FileContent
from wflow_api.models.documents import (
    Comment,
    Document,
    DocumentBase,
    DocumentEvent,
    DocumentType,
    DocumentTypeFull,
)
from wflow_api.operation import operation


@operation
async def list_documents(
    client: WflowClient,
    organization: OrgSlug,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[DocumentBase]:
    """Documents in the workspace — invoices, contracts, orders and cash slips.

    The starting point for any question about what a workspace contains. Use `query` to
    narrow by amount, partner, date or status; use `get_document` for the full record
    once you have an id. Note there is no `search` argument on this endpoint.

    Fields:

    - `number`, `serie`, `internalCode`, `variableSymbol` — how the document is identified
    - `issueDate`, `dueDate`, `vatDate`, `acceptDate` — the dates that drive approval
      and payment deadlines
    - `totalAmount`, `taxExclusiveAmount`, `currency`, `exchangeRate` — the money
    - `partnerName`, `partnerIC`, `partnerVAT` — who it is with
    - `approvalStatus`, `flowStatus`, `locked`, `removed` — where it is in its lifecycle
    - `type`, `tags`, `createdBy`, `created`, `updated`
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/documents",
        params=query_params(sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[DocumentBase].model_validate(payload or {})


@operation
async def get_document(client: WflowClient, organization: OrgSlug, documentId: str) -> Document:
    """One document in full, including its lines, VAT breakdown and accounting.

    `list_documents` returns a summary; this adds the lines and the resolved register
    records a summary only names.

    Fields: beyond those on the list summary —

    - `lines` — the document lines, each with description, quantity, unit price, VAT
      and its own accounting dimensions
    - `vaTs` — the VAT breakdown per rate
    - `accounting` — how the document is posted
    - `partner`, `deliveryLocation` — the resolved register records; the list summary
      carries only the names copied onto the document

    Already on the list summary, not new here: `serie` (also a resolved record, not a
    string), `payment`, `series` (a deprecated code, distinct from `serie`), `source`
    and `dataSource`.
    """
    return Document.model_validate(
        await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}") or {}
    )


@operation
async def get_document_metadata(client: WflowClient, organization: OrgSlug, documentId: str) -> dict[str, Any]:
    """Raw extraction metadata for a document — what wflow read off the source file.

    Returned untyped on purpose: the spec describes the response only as "Metadata as
    JSON string" and publishes no schema for it, so the shape is whatever wflow sends —
    including, per that description, a JSON-encoded string rather than an object, which
    this operation decodes for you. Treat the keys as unstable.

    Fields: undocumented upstream. Inspect what comes back rather than assuming.
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/metadata") or {}
    # The spec calls this "Metadata as JSON string", so it may arrive double-encoded.
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return {"metadata": payload}
    return payload if isinstance(payload, dict) else {"metadata": payload}


@operation
async def list_document_events(client: WflowClient, organization: OrgSlug, documentId: str) -> list[DocumentEvent]:
    """The audit trail of one document — every change, approval and file event, in order.

    Read this to reconstruct what happened to a document and who did it, rather than
    just its current state.

    Fields:

    - `type` — e.g. Create, Update, Approved, Rejected, FileAdded, ChangedFlowStatus
    - `identity` — who triggered the event, when known
    - `info` — free-text detail
    - `created` — when it happened
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/events") or []
    return [DocumentEvent.model_validate(item) for item in payload]


@operation
async def list_documents_to_export(
    client: WflowClient, organization: OrgSlug, typeId: str | None = None, exclude: bool | None = None
) -> list[str]:
    """Ids of documents ready to export to an ERP or accounting system.

    Fields: a bare array of document ids, in no typed shape to model.

    - `typeId` — restrict to one document type
    - `exclude` — when true, ignore the document type's own "exclude from standard
      integration into ERP" setting and return everything otherwise ready
    """
    path = f"/api/{organization}/documents/toexport"
    payload = await client.request("GET", path, params=query_params(typeId=typeId, exclude=exclude)) or []
    return ensure_list(path, payload)


@operation
async def list_documents_to_extract(client: WflowClient, organization: OrgSlug) -> list[str]:
    """Ids of documents queued for data extraction from their source file.

    Fields: a bare array of document ids, in no typed shape to model.
    """
    path = f"/api/{organization}/documents/toextract"
    payload = await client.request("GET", path) or []
    return ensure_list(path, payload)


@operation
async def list_document_comments(client: WflowClient, organization: OrgSlug, documentId: str) -> list[Comment]:
    """The comment thread on one document.

    Fields:

    - `author` — who wrote it
    - `text`, `markdown` — the comment content, plain and formatted
    - `created`, `updated`, `removed`
    - `teams` — which teams the comment is visible to, and whether each has resolved it
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/comments") or []
    return [Comment.model_validate(item) for item in payload]


@operation
async def list_document_links(client: WflowClient, organization: OrgSlug, documentId: str) -> list[DocumentBase]:
    """Other documents linked to this one, e.g. an order linked to the invoice it produced.

    Each item is a full document summary, the same shape `list_documents` returns, not
    just an id — use it directly rather than following up with `get_document`. `created`
    and `updated` are null on these summaries; `get_document` has them.

    Fields: see `list_documents`.
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/links") or []
    return [DocumentBase.model_validate(item) for item in payload]


@operation
async def get_document_rights(client: WflowClient, organization: OrgSlug, documentId: str) -> list[TeamBase]:
    """The teams allowed to see and act on one document.

    Fields:

    - `name`, `description` — the team as shown in wflow
    - `system` — true for a built-in team rather than one the organization created
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/rights") or []
    return [TeamBase.model_validate(item) for item in payload]


@operation
async def get_document_type(client: WflowClient, organization: OrgSlug, typeId: str) -> DocumentTypeFull:
    """One document type in full, including who has access to it.

    `list_document_types` returns the summary; this adds the per-user permissions.

    Fields: beyond those on the list summary —

    - `users` — each user granted access, and their permission: All, OnlyAssigned
      or FullAccess
    """
    # The published path segment is literal, not a parameter; typeId is a query argument.
    payload = await client.request(
        "GET", f"/api/{organization}/documents/types/typeid:guid", params=query_params(typeId=typeId)
    )
    return DocumentTypeFull.model_validate(payload or {})


@operation
async def list_document_types(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[DocumentType]:
    """Document types configured in the workspace — the kinds a document may be filed as.

    Look here to learn which numbering series and sequence a type uses before assigning
    it, or to resolve the `type` field seen on a document. For one type's full detail,
    including who may use it, follow up with `get_document_type`.

    Fields:

    - `name`, `kind` — the type as shown in wflow, and the document kind it applies to
    - `default` — used automatically when a document arrives with no type set
    - `erpExclude` — excluded from standard integration into an ERP
    - `docCreatingMethod` — Upload or Manually
    - `autoStamp` — when wflow time-stamps a file of this type: None, New or Approved
    - `serie`, `sequence` — the numbering series and counter this type draws on
    - `invoiceType` — TaxInvoice, CreditNote, DebitNote, Proforma or TaxInvoicePayment
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/documents/types",
            params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
        )
        or {}
    )
    return Paged[DocumentType].model_validate(payload)


@operation
async def delete_document(client: WflowClient, organization: OrgSlug, documentId: str) -> WriteResult:
    """Delete one document, with everything attached to it.

    Its files, comments, properties and approval history go with it, and wflow keeps no
    version history to restore it from. Read `get_document` first if you are not certain
    which document the id refers to.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents"
    """
    await client.request("DELETE", f"/api/{organization}/documents/{path_segment(documentId)}")
    return WriteResult(action="deleted", resource="documents")


@operation
async def unlink_document(
    client: WflowClient, organization: OrgSlug, documentId: str, linkedDocumentId: str
) -> WriteResult:
    """Remove the link between two documents, leaving both documents in place.

    Only the association goes. `list_document_links` returns the documents currently
    linked to `documentId`, each as a full summary, so take `linkedDocumentId` from its
    `id`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/links"
    """
    await client.request(
        "DELETE", f"/api/{organization}/documents/{path_segment(documentId)}/links/{path_segment(linkedDocumentId)}"
    )
    return WriteResult(action="deleted", resource="documents/links")


@operation
async def delete_document_type(client: WflowClient, organization: OrgSlug, typeId: str) -> WriteResult:
    """Delete one of the workspace's document types.

    A type is workspace configuration shared by every document filed as it, not a
    property of one document, so this reaches further than the id suggests. Get the id
    from `list_document_types`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/types"
    """
    # The published path segment is literal, not a parameter; typeId is a query argument.
    await client.request(
        "DELETE", f"/api/{organization}/documents/types/typeid:guid", params=query_params(typeId=typeId)
    )
    return WriteResult(action="deleted", resource="documents/types")


@operation
async def lock_document(client: WflowClient, organization: OrgSlug, documentId: str, value: bool) -> WriteResult:
    """Lock or unlock a document, so it cannot be changed while someone works on it.

    Pass `value` true to lock, false to release. A locked document rejects writes until
    it is unlocked; `update_document` can override that with `ignoreLock`.
    `list_documents` reports the current state as `locked`.

    Fields: on the result —

    - `action` — "locked" or "unlocked"
    - `resource` — "documents/lock"
    """
    await client.request("PUT", f"/api/{organization}/documents/{path_segment(documentId)}/lock/{str(value).lower()}")
    return WriteResult(action="locked" if value else "unlocked", resource="documents/lock")


@operation
async def link_document(
    client: WflowClient, organization: OrgSlug, documentId: str, linkedDocumentId: str
) -> WriteResult:
    """Link one document to another, e.g. an order to the invoice it produced.

    Only the association is created; both documents stay as they are.
    `list_document_links` then returns the linked document among `documentId`'s links,
    and `unlink_document` takes the link off again.

    Fields: on the result —

    - `action` — "linked"
    - `resource` — "documents/links"
    """
    await client.request(
        "PUT", f"/api/{organization}/documents/{path_segment(documentId)}/links/{path_segment(linkedDocumentId)}"
    )
    return WriteResult(action="linked", resource="documents/links")


@operation
async def create_document_task(client: WflowClient, organization: OrgSlug, documentId: str, type: str) -> WriteResult:
    """Queue work on a document — extracting its data, or exporting it onward.

    `type` is "Extract" or "Export"; another value is rejected outright. The task is
    queued rather than run here — `list_documents_to_extract` and
    `list_documents_to_export` list the documents waiting, and whatever performs the
    work closes the task with `set_document_task_processed`. An Export task closed with
    `success` true moves the document on in its workflow (e.g. from SentToReview to
    SentToERP), which is permanent: nothing moves it back.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "documents/task"
    """
    await client.request("POST", f"/api/{organization}/documents/{path_segment(documentId)}/task/{path_segment(type)}")
    return WriteResult(action="created", resource="documents/task")


@operation
async def set_document_task_processed(
    client: WflowClient, organization: OrgSlug, documentId: str, taskType: str, success: bool
) -> WriteResult:
    """Record that a document task has been dealt with, and whether it worked.

    This is the other half of `create_document_task`: `taskType` is "Extract" or
    "Export", and `success` false records a failed attempt rather than leaving the
    document queued. Send it from whatever performed the work. Closing an Export task
    with `success` true moves the document on in its workflow (e.g. from SentToReview to
    SentToERP), which is permanent: nothing moves it back.

    Fields: on the result —

    - `action` — "processed"
    - `resource` — "documents/task"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/task/{path_segment(taskType)}/processed",
        params=query_params(success=success),
    )
    return WriteResult(action="processed", resource="documents/task")


@operation
async def update_document(
    client: WflowClient,
    organization: OrgSlug,
    document: DocumentUpdate,
    externalId: Annotated[
        str | None, Field(default=None, description="Match an existing document by your ERP's id")
    ] = None,
    ignoreLock: Annotated[bool | None, Field(default=None, description="Write even if the document is locked")] = None,
    setAsFilled: Annotated[bool | None, Field(default=None, description="Mark the document as fully filled in")] = None,
) -> WriteResult:
    """Create a document, or replace an existing one's contents.

    Matched by the `id` inside `document`, or by the `externalId` argument when
    reconciling against an ERP. Send the full record: do not rely on a field you leave
    out being kept, and `lines` and `vaTs` are whole lists regardless, so a line you omit
    is gone. `get_document` returns the record in full — read it first when
    changing a document that exists, and send back the fields this operation declares rather
    than the whole read, which also carries the status, timestamps and resolved register
    records that only a read has. `ignoreLock` overrides a lock set by `lock_document`.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents"
    - `id` — the document's id, which wflow returns for this endpoint
    """
    created = await client.request(
        "PUT",
        f"/api/{organization}/documents",
        params=query_params(externalId=externalId, ignoreLock=ignoreLock, setAsFilled=setAsFilled),
        json=write_json(document),
    )
    return WriteResult(action="updated", resource="documents", id=created)


@operation
async def update_document_metadata(
    client: WflowClient, organization: OrgSlug, documentId: str, metadata: str
) -> WriteResult:
    """Replace the extraction metadata wflow holds for one document.

    `metadata` is a string, not an object: it travels as a JSON string body, so pass JSON
    already encoded and wflow stores the text you gave. It replaces the whole blob rather
    than merging into it, and wflow keeps no version history, so read
    `get_document_metadata` first if any of what is there matters.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/metadata"
    """
    await client.request("PUT", f"/api/{organization}/documents/{path_segment(documentId)}/metadata", json=metadata)
    return WriteResult(action="updated", resource="documents/metadata")


@operation
async def update_document_payments(
    client: WflowClient, organization: OrgSlug, documentId: str, payments: list[PaymentCreate]
) -> WriteResult:
    """Replace the payments recorded against one document.

    The list you send becomes the document's payments, so a payment you leave out is
    gone. wflow publishes no read for the individual payments — `get_document`'s
    `payment` is a rollup of paid amount, date and status — so nothing can reconstruct
    what a partial payload dropped. Send every payment you mean to keep.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/payments"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/payments",
        json=write_json_list(payments),
    )
    return WriteResult(action="updated", resource="documents/payments")


@operation
async def update_document_type(
    client: WflowClient, organization: OrgSlug, documentType: DocumentTypeFull
) -> WriteResult:
    """Create a document type, or replace an existing one's configuration.

    A type is workspace configuration shared by every document filed as it, not a
    property of one document. Matched by the `id` inside `documentType`; the submitted
    object replaces the stored type, so a field you leave out can be cleared, and `users`
    is a whole set — a user you omit loses access to the type and to every document filed
    as it. That includes you: leave the caller (`id` from `get_me`) out of `users`
    and `create_document_with_files` refuses to file anything as this type, because the
    caller no longer has access to it. `get_document_type` returns it in full,
    `users` included; read it first when changing a type that exists.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/types"
    - `id` — the document type's id
    """
    created = await client.request(
        "PUT",
        f"/api/{organization}/documents/types",
        json=write_json(documentType),
    )
    return WriteResult(action="updated", resource="documents/types", id=created)


@operation
async def set_document_rights(
    client: WflowClient, organization: OrgSlug, documentId: str, teams: list[TeamBase]
) -> WriteResult:
    """Replace the set of teams allowed to see and act on one document.

    The list you send becomes the document's rights, so a team you leave out loses
    access, and an empty list leaves the document visible to nobody but full-access
    users. `get_document_rights` returns every team currently allowed, in one array —
    read it first and send its records straight back, minus the ones you are removing.
    A team is matched by `id`, which `list_teams` also returns.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "documents/rights"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/rights",
        json=write_json_list(teams, allow_empty=True),
    )
    return WriteResult(action="updated", resource="documents/rights")


@operation
async def create_document_with_files(
    client: WflowClient,
    organization: OrgSlug,
    filename: str,
    content: bytes,
    typeId: Annotated[str | None, Field(default=None, description="Document type to file it under")] = None,
    invoiceType: Annotated[
        str | None,
        Field(default=None, description="TaxInvoice, CreditNote, DebitNote, Proforma or TaxInvoicePayment"),
    ] = None,
) -> WriteResult:
    """Create a document from a file: its bytes, and the `filename` wflow should store it under.

    This is how a scan becomes a document: wflow files it under `typeId`, which
    `list_document_types` names, and reads what it can out of the file itself — an ISDOC,
    or the QR receipt on a Slovak one — into the new document's fields. It sends one file
    per call and hands back no document id, so to attach anything further, find the new
    document with `list_documents` — `sort` of "created desc" puts it first — and pass its
    id to `upload_document_file`. A refusal for lack of access to the document type means
    the caller is not in that type's `users`, which `get_document_type` lists.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "documents/withfiles"
    """
    await client.upload(
        "POST",
        f"/api/{organization}/documents/withfiles",
        filename,
        content,
        params=query_params(typeId=typeId, invoiceType=invoiceType),
        field="uploadedFiles",
    )
    return WriteResult(action="created", resource="documents/withfiles")


@operation
async def export_documents(
    client: WflowClient,
    organization: OrgSlug,
    format: str,
    filter: StructuredFilter,
    *,
    max_bytes: int | None = None,
) -> FileContent:
    """Export a set of documents as one file, in an accounting system's own format.

    `format` is one of "byznyssolitea", "datev", "excel", "generic", "isdoc", "kros",
    "moneyerp", "moneys3", "mrp", "premier" or "xml"; another value is rejected outright.
    `filter` chooses which documents go in — `filters` per column, `propertyFilters` per
    custom property, `search` as free text — and **`sort` is required**: pass something
    like "number asc", because wflow fails the export without it, an empty `filter`
    object included. The other three are optional and default to no restriction.

    wflow streams the export file itself, whatever the format, and it comes back as its own
    bytes. With `max_bytes` set, a larger export is refused rather than truncated.

    Fields:

    - `filename` — whatever wflow's Content-Disposition names, when it sends one
    - `content_type` — the MIME type wflow gave the export
    - `content` — the export's bytes
    """
    return await client.download(
        f"/api/{organization}/documents/export/{path_segment(format)}",
        "POST",
        json=write_json(filter.with_empty_restrictions()),
        max_bytes=max_bytes,
    )
