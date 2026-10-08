"""DocumentTags tag: the free-text labels attached to documents."""

from wflow_api.client import WflowClient
from wflow_api.guards import ensure_list, path_segment
from wflow_api.models import OrgSlug, WriteResult
from wflow_api.operation import operation


@operation
async def get_document_tags(client: WflowClient, organization: OrgSlug, documentId: str) -> list[str]:
    """The tags attached to one document.

    Fields: a bare array of tag strings.
    """
    path = f"/api/{organization}/documents/{path_segment(documentId)}/tags"
    return ensure_list(path, await client.request("GET", path) or [])


@operation
async def list_document_tags(client: WflowClient, organization: OrgSlug) -> list[str]:
    """Every tag in use across the workspace's documents.

    Fields: a bare array of tag strings.
    """
    path = f"/api/{organization}/documents/tags"
    return ensure_list(path, await client.request("GET", path) or [])


@operation
async def add_document_tag(client: WflowClient, organization: OrgSlug, documentId: str, tag: str) -> WriteResult:
    """Put one tag on one document.

    `tag` is the label itself, not an id: a label the workspace has never used is
    created by being used here, so a misspelling makes a new tag rather than failing.
    `list_document_tags` shows what is already in use.

    Fields: on the result —

    - `action` — "added"
    - `resource` — "documents/tags"
    """
    await client.request("PUT", f"/api/{organization}/documents/{path_segment(documentId)}/tags/{path_segment(tag)}")
    return WriteResult(action="added", resource="documents/tags")


@operation
async def delete_document_tag(client: WflowClient, organization: OrgSlug, documentId: str, tag: str) -> WriteResult:
    """Take one tag off one document.

    `tag` is the label itself, not an id — take it from `get_document_tags`. Other
    documents keep the tag; it drops out of `list_document_tags` only once no document
    carries it any more.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/tags"
    """
    await client.request("DELETE", f"/api/{organization}/documents/{path_segment(documentId)}/tags/{path_segment(tag)}")
    return WriteResult(action="deleted", resource="documents/tags")
