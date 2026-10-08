"""DocumentFiles tag: the files attached to a document, and their content."""

from typing import Annotated

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params
from wflow_api.models import OrgSlug, WriteResult
from wflow_api.models.common import FileContent
from wflow_api.models.documents import DocumentFile
from wflow_api.operation import operation


@operation
async def list_document_files(client: WflowClient, organization: OrgSlug, documentId: str) -> list[DocumentFile]:
    """The files attached to one document — the scan or PDF, plus any annexes.

    Call this before downloading, to find out which file you want: exactly one is the
    main document and the rest are attachments.

    Fields:

    - `name` — the file name as stored
    - `main` — true for the document's primary file; `download_document_main_file`
      fetches this one without needing its id
    - `signed`, `stamped` — whether wflow has applied a signature or a stamp
    - `created` — when it was attached
    """
    payload = await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/files") or []
    return [DocumentFile.model_validate(item) for item in payload]


@operation
async def download_document_main_file(
    client: WflowClient, organization: OrgSlug, documentId: str, *, max_bytes: int | None = None
) -> FileContent:
    """Download the document's primary file — the scan or PDF the document was made from.

    Use this when you have a document id and want its content without first listing the
    attachments. The file comes back as its own bytes, exactly as wflow stores it.

    Fields:

    - `filename` — as wflow reports it, or null when it sends no name
    - `content_type` — MIME type, e.g. "application/pdf"
    - `content` — the file's bytes

    With `max_bytes` set, a larger file is refused rather than truncated. A document with no
    primary file is reported as such rather than returned empty.
    """
    return await client.download(
        f"/api/{organization}/documents/{path_segment(documentId)}/files/main/download", max_bytes=max_bytes
    )


@operation
async def download_document_file(
    client: WflowClient, organization: OrgSlug, fileId: str, *, max_bytes: int | None = None
) -> FileContent:
    """Download one specific file attached to a document, by its file id.

    Get the id from `list_document_files`. For the primary file, `download_document_main_file`
    saves a call. The file comes back as its own bytes, exactly as wflow stores it.

    Fields:

    - `filename` — as wflow reports it, or null when it sends no name
    - `content_type` — MIME type, e.g. "application/pdf"
    - `content` — the file's bytes

    With `max_bytes` set, a larger file is refused rather than truncated.
    """
    return await client.download(
        f"/api/{organization}/documents/files/{path_segment(fileId)}/download", max_bytes=max_bytes
    )


@operation
async def delete_document_file(client: WflowClient, organization: OrgSlug, fileId: str) -> WriteResult:
    """Delete one file attached to a document. The document itself stays.

    Get the id from `list_document_files`, which also flags the file marked `main`:
    deleting that one leaves the document without the scan or PDF it was made from.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/files"
    """
    await client.request("DELETE", f"/api/{organization}/documents/files/{path_segment(fileId)}")
    return WriteResult(action="deleted", resource="documents/files")


@operation
async def stamp_document_file(client: WflowClient, organization: OrgSlug, documentId: str, fileId: str) -> WriteResult:
    """Apply wflow's time stamp to one file attached to a document.

    The stamp goes into the stored file and nothing takes it off again. Only a
    PDF can be stamped; any other file is rejected as an unsupported file type.
    `list_document_files` reports which files already carry one as `stamped`, and a
    document type can stamp automatically — `list_document_types` shows that as `autoStamp`.

    Fields: on the result —

    - `action` — "stamped"
    - `resource` — "documents/files"
    """
    await client.request(
        "PUT", f"/api/{organization}/documents/{path_segment(documentId)}/files/{path_segment(fileId)}/stamp"
    )
    return WriteResult(action="stamped", resource="documents/files")


@operation
async def upload_document_file(
    client: WflowClient,
    organization: OrgSlug,
    documentId: str,
    filename: str,
    content: bytes,
    main: Annotated[bool | None, Field(default=None, description="Make this the document's primary file")] = None,
) -> WriteResult:
    """Attach a file to a document: its bytes, and the `filename` wflow should store it under.

    The file joins whatever is already attached and nothing existing is touched. `main`
    true instead makes it the document's primary file — the one
    `download_document_main_file` fetches — which displaces the file holding that place
    now; `list_document_files` says which one that is.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "documents/files"
    - `id` — the new file's id, which `stamp_document_file`, `download_document_file` and
      `delete_document_file` all take; null if wflow sends no body
    """
    created = await client.upload(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/files/upload",
        filename,
        content,
        params=query_params(main=main),
    )
    return WriteResult(action="created", resource="documents/files", id=created)
