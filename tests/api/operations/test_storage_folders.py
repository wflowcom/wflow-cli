import json

import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowError
from wflow_api.models.storage import StorageFolder
from wflow_api.operations import storage_folders


def test_a_storage_folder_knows_its_parent():
    folder = StorageFolder.model_validate({"id": "fo-2", "name": "2026", "parentId": "fo-1"})

    assert (folder.name, folder.parentId) == ("2026", "fo-1")


async def test_folder_children_take_folder_id_as_a_query_argument():
    client, requests = mock_wflow({"/api/acme/storage/folders/children": [{"id": "fo-2", "name": "2026"}]})

    result = await storage_folders.list_storage_folder_children(client, "acme", folderId="fo-1")

    assert requests[0].url.params["folderId"] == "fo-1"
    assert result[0].name == "2026"


async def test_omitting_the_folder_id_lists_the_root():
    client, requests = mock_wflow({"/api/acme/storage/folders/children": []})

    assert await storage_folders.list_storage_folder_children(client, "acme") == []
    assert "folderId" not in requests[0].url.params


async def test_one_storage_folder_is_fetched_by_id():
    client, requests = mock_wflow(
        {"/api/acme/storage/folders/fo-2": {"id": "fo-2", "name": "2026", "parentId": "fo-1", "hasChildren": True}}
    )

    result = await storage_folders.get_storage_folder(client, "acme", "fo-2")

    assert requests[0].url.path == "/api/acme/storage/folders/fo-2"
    assert (result.name, result.hasChildren) == ("2026", True)


async def test_folder_rights_are_fetched_by_folder_id():
    client, requests = mock_wflow({"/api/acme/storage/folders/fo-1/rights": [{"id": "t-1", "name": "Legal"}]})

    result = await storage_folders.get_storage_folder_rights(client, "acme", "fo-1")

    assert requests[0].url.path == "/api/acme/storage/folders/fo-1/rights"
    assert result[0].name == "Legal"


async def test_deleting_a_folder_hits_its_own_path():
    client, requests = mock_wflow({"/api/acme/storage/folders/fo-1": None})

    result = await storage_folders.delete_storage_folder(client, "acme", "fo-1")

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == "/api/acme/storage/folders/fo-1"
    assert (result.action, result.resource) == ("deleted", "storage/folders")


BODY_WRITES = [
    (
        "set_storage_folder_rights",
        {"folderId": "fo-1", "teams": [{"id": "t-1"}]},
        "PUT",
        "/api/acme/storage/folders/fo-1/rights",
        [{"id": "t-1"}],
        None,
        ("updated", "storage/folders/rights"),
    ),
    (
        "update_storage_folder",
        {"folder": {"name": "Contracts"}},
        "PUT",
        "/api/acme/storage/folders",
        {"name": "Contracts"},
        "new-id",
        ("updated", "storage/folders"),
    ),
]


@pytest.mark.parametrize("name,arguments,method,path,body,response,outcome", BODY_WRITES)
async def test_each_body_write_sends_its_own_payload(name, arguments, method, path, body, response, outcome):
    client, requests = mock_wflow({path: response})

    result = await getattr(storage_folders, name)(client, "acme", **arguments)

    assert requests[0].method == method
    assert requests[0].url.path == path
    assert json.loads(requests[0].content) == body
    assert (result.action, result.resource) == outcome
    assert result.id == response


async def test_an_empty_rights_list_is_sent_rather_than_refused():
    client, requests = mock_wflow({"/api/acme/storage/folders/fo-1/rights": None})

    result = await storage_folders.set_storage_folder_rights(client, "acme", "fo-1", [])

    assert json.loads(requests[0].content) == []
    assert result.action == "updated"


@pytest.mark.parametrize("hostile", [".", ".."])
async def test_a_folder_id_of_dots_never_reaches_the_wire(hostile):
    client, requests = mock_wflow({"/api/acme/storage": None, "/api/acme/storage/folders": None})

    with pytest.raises(WflowError, match="run of dots"):
        await storage_folders.delete_storage_folder(client, "acme", hostile)

    assert requests == []
