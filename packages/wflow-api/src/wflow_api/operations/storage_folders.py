"""StorageFolders tag: the archive's folder tree."""

from typing import Annotated

from pydantic import Field

from wflow_api.client import WflowClient
from wflow_api.guards import path_segment, query_params, write_json, write_json_list
from wflow_api.models import OrgSlug, StorageFolder, StorageFolderUpdate, TeamBase, WriteResult
from wflow_api.operation import operation


@operation
async def list_storage_folder_children(
    client: WflowClient,
    organization: OrgSlug,
    folderId: Annotated[str | None, Field(default=None, description="Omit to list the root")] = None,
) -> list[StorageFolder]:
    """The folders directly inside one storage folder — one level, not the whole tree.

    Omit `folderId` to start at the root, then walk down by passing the id of the folder
    you want to open. Call it repeatedly to descend; there is no recursive listing.

    Fields:

    - `id` — pass back in to descend, or to `get_storage_folder` and `get_storage_folder_rights`
    - `parentId` — the folder this one sits inside; null at the root
    - `name` — the folder name
    - `fullPath` — the folder's full path, so a caller can show where it sits without walking back up
    - `hasChildren` — whether descending further will return anything
    """
    payload = (
        await client.request(
            "GET",
            f"/api/{organization}/storage/folders/children",
            params=query_params(folderId=folderId),
        )
        or []
    )
    return [StorageFolder.model_validate(item) for item in payload]


@operation
async def get_storage_folder(client: WflowClient, organization: OrgSlug, folderId: str) -> StorageFolder:
    """One storage folder in full, by its folder id.

    Get the id from `list_storage_folder_children`.

    Fields: see `list_storage_folder_children`.
    """
    payload = await client.request("GET", f"/api/{organization}/storage/folders/{path_segment(folderId)}") or {}
    return StorageFolder.model_validate(payload)


@operation
async def get_storage_folder_rights(client: WflowClient, organization: OrgSlug, folderId: str) -> list[TeamBase]:
    """The teams allowed to see and act on one storage folder.

    Fields:

    - `name`, `description` — the team as shown in wflow
    - `system` — true for a built-in team rather than one the organization created
    """
    payload = await client.request("GET", f"/api/{organization}/storage/folders/{path_segment(folderId)}/rights") or []
    return [TeamBase.model_validate(item) for item in payload]


@operation
async def delete_storage_folder(client: WflowClient, organization: OrgSlug, folderId: str) -> WriteResult:
    """Delete one storage folder.

    A folder holds both files and further folders, and `hasChildren` on
    `list_storage_folder_children` only accounts for the folders. Check what is inside
    before deleting; `list_storage_files` reports each file's `folderId`.

    Fields: on the result —

    - `action` — "deleted"
    - `resource` — "storage/folders"
    """
    await client.request("DELETE", f"/api/{organization}/storage/folders/{path_segment(folderId)}")
    return WriteResult(action="deleted", resource="storage/folders")


@operation
async def set_storage_folder_rights(
    client: WflowClient, organization: OrgSlug, folderId: str, teams: list[TeamBase]
) -> WriteResult:
    """Replace the set of teams allowed to see and act on one storage folder.

    The list you send becomes the folder's rights, so a team you leave out loses access,
    and an empty list leaves the folder visible to nobody but full-access users.
    `get_storage_folder_rights` returns every team currently allowed, in one array — read
    it first and send back everyone you mean to keep. A team is identified by its `id`,
    which `list_teams` also returns.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/folders/rights"
    """
    await client.request(
        "PUT",
        f"/api/{organization}/storage/folders/{path_segment(folderId)}/rights",
        json=write_json_list(teams, allow_empty=True),
    )
    return WriteResult(action="updated", resource="storage/folders/rights")


@operation
async def update_storage_folder(client: WflowClient, organization: OrgSlug, folder: StorageFolderUpdate) -> WriteResult:
    """Create a storage folder, or replace an existing one's name and place in the tree.

    Matched by the `id` inside `folder`; omit `id` to create, and omit `parentId` on a
    new folder to put it at the root. The submitted object replaces the stored folder, so
    send the full record when changing one that exists: a field you leave out can be
    cleared, and for `parentId` that is the folder's place in the tree.
    `get_storage_folder` returns what is stored today, plus a `fullPath` and `hasChildren`
    it computes; send back the other three.

    Fields: on the result —

    - `action` — "updated"
    - `resource` — "storage/folders"
    - `id` — the folder's id
    """
    created = await client.request(
        "PUT",
        f"/api/{organization}/storage/folders",
        json=write_json(folder),
    )
    return WriteResult(action="updated", resource="storage/folders", id=created)
