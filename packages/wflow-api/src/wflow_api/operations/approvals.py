"""DocumentApprovals and ApprovalsTemplates tags: approval workflows and the templates they run."""

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params, write_json
from wflow_api.models import (
    ApprovalsTemplate,
    ApprovalsTemplateFull,
    ApprovalsTemplateTeams,
    ApprovalsTemplateUpdate,
    OrgSlug,
    Page,
    Paged,
    PageSize,
    Query,
    Search,
    Sort,
    WriteResult,
)
from wflow_api.models.documents import ApprovalProcess
from wflow_api.operation import operation


@operation
async def get_document_approvals(client: WflowClient, organization: OrgSlug, documentId: str) -> ApprovalProcess:
    """The approval path assigned to one document, and its progress so far.

    Fields:

    - `pathName` — the name of the approval template applied
    - `items` — one entry per level, each with the assigned `team` or `identity`,
      its `status` (NotApproved, Approved, Rejected, Returned or None) and, once
      acted on, the `date`
    """
    return ApprovalProcess.model_validate(
        await client.request("GET", f"/api/{organization}/documents/{path_segment(documentId)}/approvals") or {}
    )


@operation
async def get_storage_file_approvals(client: WflowClient, organization: OrgSlug, fileId: str) -> ApprovalProcess:
    """The approval path assigned to one archived file, and its progress so far.

    Same shape as `get_document_approvals`, for a storage file instead of an approval
    document. Get the id from `list_storage_files`.

    Fields: see `get_document_approvals`.
    """
    return ApprovalProcess.model_validate(
        await client.request("GET", f"/api/{organization}/storage/files/{path_segment(fileId)}/approvals") or {}
    )


@operation
async def list_approval_templates(
    client: WflowClient,
    organization: OrgSlug,
    search: Search = None,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[ApprovalsTemplate]:
    """Approval templates configured in the workspace — the approval paths documents follow.

    Fields:

    - `id` — pass to `get_approval_template`
    - `name`
    - `isEmpty` — true when the template defines no approval steps
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/approvalstemplates",
        params=query_params(search=search, sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[ApprovalsTemplate].model_validate(payload or {})


@operation
async def get_approval_template(client: WflowClient, organization: OrgSlug, templateId: str) -> ApprovalsTemplateFull:
    """One approval template in full, by its template id.

    Get the id from `list_approval_templates`.

    Fields: beyond those on the list summary —

    - `teams` — each assigned team's id and its `level` in the approval process
    - `accessTeams` — team ids granted access automatically once the template applies
    - `conditionFolders` — storage folder ids this template's conditional assignment
      applies to
    - `validationLockLevel`
    """
    payload = await client.request("GET", f"/api/{organization}/approvalstemplates/{path_segment(templateId)}") or {}
    return ApprovalsTemplateFull.model_validate(payload)


@operation
async def delete_approval_template(client: WflowClient, organization: OrgSlug, templateId: str) -> WriteResult:
    """Delete one approval template — an approval path the workspace can assign.

    The template is workspace configuration, not one document's approval process: this
    removes the path itself, for everything that would have used it. To take the path off
    a single document, use `delete_document_approval_path`. Get the id from
    `list_approval_templates`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "approvalstemplates"
    """
    await client.request("DELETE", f"/api/{organization}/approvalstemplates/{path_segment(templateId)}")
    return WriteResult(action="deleted", resource="approvalstemplates")


@operation
async def delete_document_approval_path(client: WflowClient, organization: OrgSlug, documentId: str) -> WriteResult:
    """Take the approval path off one document.

    The template it was assigned from is untouched; what goes is this document's approval
    process, including the approvals already recorded on it that
    `get_document_approvals` returns. The document itself stays.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "documents/approvals"
    """
    await client.request("DELETE", f"/api/{organization}/documents/{path_segment(documentId)}/approvals")
    return WriteResult(action="deleted", resource="documents/approvals")


@operation
async def delete_storage_file_approval_path(client: WflowClient, organization: OrgSlug, fileId: str) -> WriteResult:
    """Take the approval path off one archived file.

    The same as `delete_document_approval_path`, for a storage file instead of an
    approval document: the template survives, this file's approval process does not. Get
    the id from `list_storage_files`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "storage/files/approvals"
    """
    await client.request("DELETE", f"/api/{organization}/storage/files/{path_segment(fileId)}/approvals")
    return WriteResult(action="deleted", resource="storage/files/approvals")


@operation
async def set_storage_file_approval_path(
    client: WflowClient, organization: OrgSlug, fileId: str, templateId: str
) -> WriteResult:
    """Put one archived file through the approval path a template describes.

    Get `templateId` from `list_approval_templates`; to take the path off rather than
    swap it, use `delete_storage_file_approval_path`. Read `get_storage_file_approvals`
    first where a process is already running: a file that already has a path may be
    refused or may have its path replaced, so take the old path off with
    `delete_storage_file_approval_path` first rather than relying on either outcome.

    Fields: on the result —

    - `action` — "set"
    - `resource` — "storage/files/approvals"
    """
    await client.request(
        "PUT", f"/api/{organization}/storage/files/{path_segment(fileId)}/approvals/set/{path_segment(templateId)}"
    )
    return WriteResult(action="set", resource="storage/files/approvals")


@operation
async def update_approval_template(
    client: WflowClient, organization: OrgSlug, template: ApprovalsTemplateUpdate
) -> WriteResult:
    """Create an approval template, or replace an existing one's steps.

    A template is workspace configuration, not one document's process: this reaches
    everything the path is assigned to. Matched by the `id` inside `template`. `teams`,
    `accessTeams` and `conditionFolders` are whole sets — a team you leave out is no
    longer part of the path at any level — and send the rest of the template with them:
    a field you omit, `validationLockLevel` included, is cleared rather than kept, so the
    whole record is the only correct payload.
    `get_approval_template` returns all three — read it first and send back
    everything you mean to keep, leaving out its `isEmpty`, which the read computes and
    this operation does not write. Each entry in `teams` is a team id from `list_teams` plus
    the `level` it approves at.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "approvalstemplates"
    - `id` — the template's id
    """
    created = await client.request(
        "PUT",
        f"/api/{organization}/approvalstemplates",
        json=write_json(template),
    )
    return WriteResult(action="updated", resource="approvalstemplates", id=created)


@operation
async def set_document_approval_path(
    client: WflowClient,
    organization: OrgSlug,
    documentId: str,
    templateId: str,
    teams: ApprovalsTemplateTeams | None = None,
) -> WriteResult:
    """Put one document through the approval path a template describes.

    **It does not overwrite an existing path — it refuses.** A document already on a path
    is rejected with an error saying so, so swapping a path means calling
    `delete_document_approval_path` first; this operation only ever sets a path on a document
    that has none. Get `templateId` from `list_approval_templates`.

    Omit `teams` to apply the template as it is configured: the template's own teams
    appear on the document. Sent, `teams` replaces the template's assignment for this
    document rather than adding to it, so name every level you mean to keep — and read
    `get_document_approvals` back afterwards, because the level a team lands on is not
    guaranteed to be the level you sent.

    Fields: on the result —

    - `action` — "set"
    - `resource` — "documents/approvals"
    """
    # httpx sends no body for json=None; `{}` would bind as teams=null, a different instruction.
    await client.request(
        "PUT",
        f"/api/{organization}/documents/{path_segment(documentId)}/approvals/set/{path_segment(templateId)}",
        json=write_json(teams) if teams is not None else None,
    )
    return WriteResult(action="set", resource="documents/approvals")
