"""StorageFiles tag: the document archive, separate from approval documents."""

from typing import Annotated

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params, write_definitions_json, write_json, write_json_list
from wflow_api.models import (
    OrgSlug,
    Page,
    Paged,
    PageSize,
    PropertyUpdate,
    Query,
    Sort,
    StorageFile,
    TeamBase,
    WriteResult,
)
from wflow_api.models.common import FileContent
from wflow_api.models.documents import Property, PropertyDefinition
from wflow_api.operation import operation


@operation
async def list_storage_files(
    client: WflowClient,
    organization: OrgSlug,
    sort: Sort = None,
    query: Query = None,
    pageSize: PageSize = None,
    page: Page = None,
) -> Paged[StorageFile]:
    """Files in the workspace's document storage — its archive, organised into folders.

    Storage is separate from approval documents, which `list_documents` returns: a
    contract or a certificate lives here, an invoice going through approval lives there.
    If the user asks about invoices or approvals, this is the wrong operation. Note there
    is no `search` argument on this endpoint. Removed files are
    not returned and cannot be filtered for; note a file's id before deleting it if it may
    need `restore_storage_file`.

    Fields:

    - `id` — pass to `get_storage_file` and `download_storage_file`
    - `name`, `description` — how the file is labelled
    - `locked` — whether it is checked out and cannot be changed
    - `approvalStatus` — NotApproved, Approved, Rejected, Returned or None
    - `folderId` — the folder it lives in
    - `location` — where it is stored
    - `removed` — the date it was removed, when it has been
    - `created`, `updated` — when it was archived and last touched
    """
    payload = await client.request(
        "GET",
        f"/api/{organization}/storage/files",
        params=query_params(sort=sort, query=query, pageSize=pageSize, page=page),
    )
    return Paged[StorageFile].model_validate(payload or {})


@operation
async def get_storage_file(client: WflowClient, organization: OrgSlug, fileId: str) -> StorageFile:
    """One archived file in full, by its storage file id.

    Get the id from `list_storage_files`.

    Fields: see `list_storage_files`.
    """
    payload = await client.request("GET", f"/api/{organization}/storage/files/{path_segment(fileId)}") or {}
    return StorageFile.model_validate(payload)


@operation
async def download_storage_file(
    client: WflowClient, organization: OrgSlug, fileId: str, *, max_bytes: int | None = None
) -> FileContent:
    """Download one archived file's content, by its storage file id.

    Get the id from `list_storage_files`. For a file attached to an approval document,
    use `download_document_file` instead.

    Fields:

    - `filename` — as wflow reports it, or null when it sends no name
    - `content_type` — MIME type, e.g. "application/pdf"
    - `content` — the file's bytes, exactly as wflow stores them

    `max_bytes`, when given, refuses a larger file before it is read in full; without it
    any size comes through.
    """
    return await client.download(
        f"/api/{organization}/storage/files/{path_segment(fileId)}/download", max_bytes=max_bytes
    )


@operation
async def get_storage_file_properties(client: WflowClient, organization: OrgSlug, fileId: str) -> list[Property]:
    """The custom property values set on one archived file.

    A workspace defines its custom properties once with
    `list_storage_file_property_definitions`; this is what a specific file holds for
    each of them.

    Fields:

    - `name`, `type` — the definition this value belongs to
    - `value` — what this file holds for the property
    - `order`, `show`, `editable`, `kinds` — the definition's own presentation and
      applicability settings, echoed alongside the value
    """
    payload = await client.request("GET", f"/api/{organization}/storage/files/{path_segment(fileId)}/properties") or []
    return [Property.model_validate(item) for item in payload]


@operation
async def get_storage_file_property_definition(
    client: WflowClient, organization: OrgSlug, id: str
) -> PropertyDefinition:
    """One custom property definition for archived files, by its id.

    Use `list_storage_file_property_definitions` to find the id, or resolve one already
    seen on a file's `get_storage_file_properties` result.

    Fields:

    - `name`, `type` — how the property is labelled and what kind of value it holds
    - `order`, `show` — where it appears, and whether it is shown at all
    - `editable` — whether a file's value for it can be changed
    - `kinds` — which document kinds it applies to
    """
    payload = (
        await client.request("GET", f"/api/{organization}/storage/files/properties/definition/{path_segment(id)}") or {}
    )
    return PropertyDefinition.model_validate(payload)


@operation
async def list_storage_file_property_definitions(
    client: WflowClient, organization: OrgSlug
) -> list[PropertyDefinition]:
    """Every custom property defined for archived files in the workspace.

    Call this to learn what custom fields exist before reading or interpreting the
    values `get_storage_file_properties` returns for a specific file.

    Fields:

    - `name`, `type` — how the property is labelled and what kind of value it holds
    - `order`, `show` — where it appears, and whether it is shown at all
    - `editable` — whether a file's value for it can be changed
    - `kinds` — which document kinds it applies to
    """
    payload = await client.request("GET", f"/api/{organization}/storage/files/properties/definitions") or []
    return [PropertyDefinition.model_validate(item) for item in payload]


@operation
async def get_storage_file_rights(client: WflowClient, organization: OrgSlug, fileId: str) -> list[TeamBase]:
    """The teams allowed to see and act on one archived file.

    Fields:

    - `name`, `description` — the team as shown in wflow
    - `system` — true for a built-in team rather than one the organization created
    """
    payload = await client.request("GET", f"/api/{organization}/storage/files/{path_segment(fileId)}/rights") or []
    return [TeamBase.model_validate(item) for item in payload]


@operation
async def delete_storage_file(client: WflowClient, organization: OrgSlug, fileId: str) -> WriteResult:
    """Delete one archived file.

    This is the archive, not the approval documents: for a file attached to a document,
    use `delete_document_file`. Get the id from
    `list_storage_files`. `restore_storage_file` brings the file back only by this id, and
    once deleted it no longer appears in `list_storage_files` and `get_storage_file`
    answers a record of nulls for it, so keep the id if it may need restoring.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "storage/files"
    """
    await client.request("DELETE", f"/api/{organization}/storage/files/{path_segment(fileId)}")
    return WriteResult(action="deleted", resource="storage/files")


@operation
async def delete_storage_file_property(
    client: WflowClient, organization: OrgSlug, fileId: str, propertyId: str
) -> WriteResult:
    """Clear one custom property value from one archived file.

    Only this file's value goes; the definition stays and every other file keeps its own
    value. Get `propertyId` from the `id` of the entry in `get_storage_file_properties`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "storage/files/properties"
    """
    await client.request(
        "DELETE", f"/api/{organization}/storage/files/{path_segment(fileId)}/properties/{path_segment(propertyId)}"
    )
    return WriteResult(action="deleted", resource="storage/files/properties")


@operation
async def delete_storage_file_property_definition(client: WflowClient, organization: OrgSlug, id: str) -> WriteResult:
    """Delete one archived-file custom property definition from the workspace.

    This is the definition itself, not one file's value for it: the property stops
    existing for every archived file at once. To clear a single file's value, use
    `delete_storage_file_property`. Get the id from
    `list_storage_file_property_definitions`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "storage/files/properties/definition"
    """
    await client.request("DELETE", f"/api/{organization}/storage/files/properties/definition/{path_segment(id)}")
    return WriteResult(action="deleted", resource="storage/files/properties/definition")


@operation
async def lock_storage_file(client: WflowClient, organization: OrgSlug, fileId: str, value: bool) -> WriteResult:
    """Lock or unlock an archived file, so it cannot be changed while someone works on it.

    Pass `value` true to lock, false to release. `list_storage_files` reports the current
    state as `locked`. This is the archive: for a file attached to an approval document,
    lock the document with `lock_document`.

    Fields: on the result —

    - `action` — "locked" or "unlocked"
    - `resource` — "storage/files/lock"
    """
    await client.request("PUT", f"/api/{organization}/storage/files/{path_segment(fileId)}/lock/{str(value).lower()}")
    return WriteResult(action="locked" if value else "unlocked", resource="storage/files/lock")


@operation
async def move_storage_file(client: WflowClient, organization: OrgSlug, fileId: str, folderId: str) -> WriteResult:
    """Move an archived file into a different folder.

    The file keeps its id, name and properties. Teams granted on the file itself may not
    survive the move: read `get_storage_file_rights` before it and, if the list changed,
    send it back with `set_storage_file_rights` after. Use `list_storage_folder_children`
    to find the target folder's id.

    Fields: on the result —

    - `action` — "moved"
    - `resource` — "storage/files"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/move",
        params=query_params(folderId=folderId),
    )
    return WriteResult(action="moved", resource="storage/files")


@operation
async def rename_storage_file(client: WflowClient, organization: OrgSlug, fileId: str, name: str) -> WriteResult:
    """Rename an archived file.

    `name` replaces the old one outright, and wflow keeps no version history to read it
    back from, so check `get_storage_file` first if the current name matters. Nothing
    else about the file changes, and its id stays valid.

    Fields: on the result —

    - `action` — "renamed"
    - `resource` — "storage/files"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/rename",
        params=query_params(name=name),
    )
    return WriteResult(action="renamed", resource="storage/files")


@operation
async def restore_storage_file(client: WflowClient, organization: OrgSlug, fileId: str, folderId: str) -> WriteResult:
    """Bring a removed file back into the archive, into the folder you name.

    Removed files are not listed, so `fileId` must be the id noted before
    `delete_storage_file` was called. This puts the file back under
    `folderId`, which need not be the folder it was removed from. Use
    `list_storage_folder_children` to find that id.

    Fields: on the result —

    - `action` — "restored"
    - `resource` — "storage/files"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/restore",
        params=query_params(folderId=folderId),
    )
    return WriteResult(action="restored", resource="storage/files")


@operation
async def set_storage_file_rights(
    client: WflowClient, organization: OrgSlug, fileId: str, teams: list[TeamBase]
) -> WriteResult:
    """Replace the set of teams allowed to see and act on one archived file.

    The list you send becomes the file's rights, so a team you leave out loses access,
    and an empty list leaves the file visible to nobody but full-access users.
    `get_storage_file_rights` returns every team currently allowed, in one array — read
    it first and send back everyone you mean to keep. A team is identified by its `id`,
    which `list_teams` also returns.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/files/rights"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/rights",
        json=write_json_list(teams, allow_empty=True),
    )
    return WriteResult(action="updated", resource="storage/files/rights")


@operation
async def update_storage_file_properties(
    client: WflowClient, organization: OrgSlug, fileId: str, properties: list[PropertyUpdate]
) -> WriteResult:
    """Replace the custom property values held on one archived file.

    The list you send becomes the file's values, so a property you leave out is cleared
    on this file. `get_storage_file_properties` returns everything it currently holds, in
    one array — read it first and send back the `id` and `value` of every entry you mean
    to keep, and nothing else: the read also carries each definition's name, type and
    presentation, which this operation does not write. To set a value for a property not defined
    yet, use `update_storage_file_properties_with_definition`.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/files/properties"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/properties",
        json=write_json_list(properties),
    )
    return WriteResult(action="updated", resource="storage/files/properties")


@operation
async def update_storage_file_properties_with_definition(
    client: WflowClient,
    organization: OrgSlug,
    fileId: str,
    properties: list[Property],
    addOnly: Annotated[
        bool | None, Field(default=None, description="Leave an existing definition alone; defaults to true")
    ] = None,
) -> WriteResult:
    """Define new custom properties and set their values on one archived file.

    Every entry must carry `id`, `name`, `type` and `value`, whether the property is new to
    the workspace or already defined: wflow refuses the whole list over an entry holding
    only `id` and `value`, so such a list is refused here before anything is sent. An
    already-defined property sent in full gets its value updated on this file; one you
    leave out keeps its value. To set values without repeating definitions, use
    `update_storage_file_properties`. `id` is a free-form string you choose; wflow keeps
    at most 30 characters of it and drops dashes, so a GUID comes back changed — pick a
    short plain id. A definition sent with only those four fields is created hidden and
    read-only (`order` 0, `show` false, `editable` false) — change that with
    `update_storage_file_property_definition`. A definition is workspace configuration, so
    that part reaches every archived file. `addOnly` defaults to true, which leaves an
    existing definition as it is; false rewrites it from what you send, for every file at
    once.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/files/properties/withdefinition"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/files/{path_segment(fileId)}/properties/withdefinition",
        params=query_params(addOnly=addOnly),
        json=write_definitions_json(properties, values_operation="update_storage_file_properties"),
    )
    return WriteResult(action="updated", resource="storage/files/properties/withdefinition")


@operation
async def update_storage_file_property_definition(
    client: WflowClient, organization: OrgSlug, definition: PropertyDefinition
) -> WriteResult:
    """Define a custom property for archived files, or replace an existing definition.

    This is workspace configuration, not one file's value: every archived file sees the
    change at once. **`id` is required and you choose it** — a free-form string, not a
    GUID wflow mints; a definition sent without one creates nothing. wflow keeps at most
    30 characters of the id and drops dashes, so a GUID comes back changed — pick a short
    plain id. The submitted object replaces the stored definition, so a field you
    leave out can be cleared, and `kinds` and `data` are whole lists — omit a document
    kind and the property stops applying there, omit a choice from `data` and it can no
    longer be picked. `get_storage_file_property_definition` returns the definition in
    full; read it first when changing one that exists.

    **Neither `type` nor `kinds` is reliably stored.** A definition sent with
    `type: "Text"` and `kinds: ["Other"]` can be accepted as a success and read back as
    `type: "UNDEFINED"` and `kinds: null`. Read the definition back and check what landed
    rather than trusting the write.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/files/properties/definition"
    - `id` — the definition's id when wflow echoes the stored definition, otherwise `null`;
      fall back to the `id` you sent
    """
    stored = await client.request(
        "PUT",
        f"/api/{organization}/storage/files/properties/definition",
        json=write_json(definition),
    )
    return WriteResult(
        action="updated",
        resource="storage/files/properties/definition",
        id=stored.get("id") if isinstance(stored, dict) else None,
    )


@operation
async def upload_storage_file(
    client: WflowClient,
    organization: OrgSlug,
    filename: str,
    content: bytes,
    folderId: Annotated[str | None, Field(default=None, description="Folder to file it in; omit for the root")] = None,
    overrideIfExists: Annotated[
        bool | None, Field(default=None, description="Overwrite a file of the same name; defaults to false")
    ] = None,
) -> WriteResult:
    """Upload a file's bytes into the archive, under the `filename` wflow should store it as.

    `folderId` picks the folder, which `list_storage_folder_children` walks. **Pass one.**
    Omitting it does not file at the root: wflow refuses the upload, so name a folder.
    When the folder already holds a file of that name, the default keeps both by storing
    this one as a numbered copy — under a name you did not choose, so take the file's id
    off the result rather than looking for it by name afterwards.
    `overrideIfExists` true overwrites that file's content instead, and nothing here can
    bring back what it held.

    Fields: on the result —

    - `action` — "created"
    - `resource` — "storage/files"
    - `id` — the stored file's id, which `get_storage_file` and the property and rights
      operations all take
    """
    created = await client.upload(
        "PUT",
        f"/api/{organization}/storage/files/upload",
        filename,
        content,
        params=query_params(folderId=folderId, overrideIfExists=overrideIfExists),
    )
    return WriteResult(action="created", resource="storage/files", id=created)
