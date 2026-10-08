import json

import pytest

from tests.helpers import mock_download, mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models import Paged
from wflow_api.models.common import FileContent
from wflow_api.models.storage import StorageFile
from wflow_api.operations import storage_files


def test_a_storage_file_carries_its_folder_and_lock_state():
    file = StorageFile.model_validate({"id": "sf-1", "name": "contract.pdf", "locked": True, "folderId": "fo-1"})

    assert (file.name, file.locked, file.folderId) == ("contract.pdf", True, "fo-1")


def test_the_collection_carries_paging():
    collection = Paged[StorageFile].model_validate(
        {"items": [{"id": "sf-1"}], "totalItems": 9, "pageSize": 1, "page": 0}
    )

    assert collection.totalItems == 9


STORAGE_FILES_BODY = {
    "items": [{"id": "sf-1", "name": "contract.pdf", "locked": False}],
    "totalItems": 1,
    "pageSize": 20,
    "page": 0,
}


async def test_storage_files_are_paged():
    client, requests = mock_wflow({"/api/acme/storage/files": STORAGE_FILES_BODY})

    result = await storage_files.list_storage_files(client, "acme", sort="name desc", pageSize=20, page=0)

    assert result.items[0].name == "contract.pdf"
    assert result.totalItems == 1
    assert dict(requests[0].url.params) == {"sort": "name desc", "pageSize": "20", "page": "0"}


async def test_one_storage_file_is_fetched_by_id():
    client, requests = mock_wflow({"/api/acme/storage/files/sf-1": {"id": "sf-1", "name": "contract.pdf"}})

    result = await storage_files.get_storage_file(client, "acme", "sf-1")

    assert requests[0].url.path == "/api/acme/storage/files/sf-1"
    assert result.name == "contract.pdf"


READS = [
    (
        "get_storage_file_properties",
        {"fileId": "sf-1"},
        "/api/acme/storage/files/sf-1/properties",
        [{"id": "p-1", "name": "Signed by", "value": "Jan"}],
        lambda result: result[0].value == "Jan",
    ),
    (
        "get_storage_file_rights",
        {"fileId": "sf-1"},
        "/api/acme/storage/files/sf-1/rights",
        [{"id": "t-1", "name": "Legal"}],
        lambda result: result[0].name == "Legal",
    ),
    (
        "get_storage_file_property_definition",
        {"id": "pd-1"},
        "/api/acme/storage/files/properties/definition/pd-1",
        {"id": "pd-1", "name": "Signed by", "type": "Text"},
        lambda result: result.name == "Signed by",
    ),
    (
        "list_storage_file_property_definitions",
        {},
        "/api/acme/storage/files/properties/definitions",
        [{"id": "pd-1", "name": "Signed by"}],
        lambda result: result[0].id == "pd-1",
    ),
]


@pytest.mark.parametrize("name,arguments,path,body,check", READS)
async def test_the_storage_file_sub_resources(name, arguments, path, body, check):
    client, requests = mock_wflow({path: body})

    result = await getattr(storage_files, name)(client, "acme", **arguments)

    assert requests[0].url.path == path
    assert check(result)


DELETES = [
    ("delete_storage_file", {"fileId": "sf-1"}, "/api/acme/storage/files/sf-1", "storage/files"),
    (
        "delete_storage_file_property",
        {"fileId": "sf-1", "propertyId": "p-1"},
        "/api/acme/storage/files/sf-1/properties/p-1",
        "storage/files/properties",
    ),
    (
        "delete_storage_file_property_definition",
        {"id": "pd-1"},
        "/api/acme/storage/files/properties/definition/pd-1",
        "storage/files/properties/definition",
    ),
]


@pytest.mark.parametrize("name,arguments,path,resource", DELETES)
async def test_each_delete_hits_its_own_path(name, arguments, path, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(storage_files, name)(client, "acme", **arguments)

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == path
    assert (result.action, result.resource) == ("deleted", resource)


PARAMETER_WRITES = [
    (
        "lock_storage_file",
        {"fileId": "sf-1", "value": True},
        "/api/acme/storage/files/sf-1/lock/true",
        {},
        ("locked", "storage/files/lock"),
    ),
    (
        "lock_storage_file",
        {"fileId": "sf-1", "value": False},
        "/api/acme/storage/files/sf-1/lock/false",
        {},
        ("unlocked", "storage/files/lock"),
    ),
    (
        "move_storage_file",
        {"fileId": "sf-1", "folderId": "fo-2"},
        "/api/acme/storage/files/sf-1/move",
        {"folderId": "fo-2"},
        ("moved", "storage/files"),
    ),
    (
        "rename_storage_file",
        {"fileId": "sf-1", "name": "renamed.pdf"},
        "/api/acme/storage/files/sf-1/rename",
        {"name": "renamed.pdf"},
        ("renamed", "storage/files"),
    ),
    (
        "restore_storage_file",
        {"fileId": "sf-1", "folderId": "fo-1"},
        "/api/acme/storage/files/sf-1/restore",
        {"folderId": "fo-1"},
        ("restored", "storage/files"),
    ),
]


@pytest.mark.parametrize("name,arguments,path,params,outcome", PARAMETER_WRITES)
async def test_each_parameter_write_builds_its_request(name, arguments, path, params, outcome):
    client, requests = mock_wflow({path: None})

    result = await getattr(storage_files, name)(client, "acme", **arguments)

    assert requests[0].method == "PUT"
    assert requests[0].url.path == path
    assert not requests[0].content
    assert dict(requests[0].url.params) == params
    assert (result.action, result.resource) == outcome


BODY_WRITES = [
    (
        "set_storage_file_rights",
        {"fileId": "sf-1", "teams": [{"id": "t-1"}]},
        "/api/acme/storage/files/sf-1/rights",
        [{"id": "t-1"}],
        None,
        ("updated", "storage/files/rights"),
    ),
    (
        "update_storage_file_properties",
        {"fileId": "sf-1", "properties": [{"id": "pd-1", "value": "Jan"}]},
        "/api/acme/storage/files/sf-1/properties",
        [{"id": "pd-1", "value": "Jan"}],
        None,
        ("updated", "storage/files/properties"),
    ),
    (
        "update_storage_file_properties_with_definition",
        {"fileId": "sf-1", "properties": [{"name": "Signed by", "type": "Text", "value": "Jan"}]},
        "/api/acme/storage/files/sf-1/properties/withdefinition",
        [{"name": "Signed by", "type": "Text", "value": "Jan"}],
        None,
        ("updated", "storage/files/properties/withdefinition"),
    ),
    (
        "update_storage_file_property_definition",
        {"definition": {"name": "Signed by", "type": "Text"}},
        "/api/acme/storage/files/properties/definition",
        {"name": "Signed by", "type": "Text"},
        {"id": "pd-1", "name": "Signed by", "type": "Text"},
        ("updated", "storage/files/properties/definition"),
    ),
]


@pytest.mark.parametrize("name,arguments,path,body,response,outcome", BODY_WRITES)
async def test_each_body_write_sends_its_own_payload(name, arguments, path, body, response, outcome):
    client, requests = mock_wflow({path: response})

    result = await getattr(storage_files, name)(client, "acme", **arguments)

    assert requests[0].method == "PUT"
    assert requests[0].url.path == path
    assert json.loads(requests[0].content) == body
    assert (result.action, result.resource) == outcome
    assert result.id == (response.get("id") if isinstance(response, dict) else response)


async def test_add_only_reaches_the_wire_under_the_name_the_spec_declares():
    path = "/api/acme/storage/files/sf-1/properties/withdefinition"
    client, requests = mock_wflow({path: None})

    await storage_files.update_storage_file_properties_with_definition(
        client, "acme", "sf-1", [{"name": "Signed by", "type": "Text", "value": "Jan"}], addOnly=False
    )

    assert requests[0].url.params["addOnly"] == "false"


async def test_the_property_definition_write_returns_the_stored_object():
    client, _ = mock_wflow(
        {"/api/acme/storage/files/properties/definition": {"id": "pd-1", "name": "Signed by", "type": "Text"}}
    )

    result = await storage_files.update_storage_file_property_definition(
        client, "acme", {"name": "Signed by", "type": "Text"}
    )

    assert result.id == "pd-1"


async def test_an_empty_rights_list_is_sent_rather_than_refused():
    client, requests = mock_wflow({"/api/acme/storage/files/sf-1/rights": None})

    result = await storage_files.set_storage_file_rights(client, "acme", "sf-1", [])

    assert json.loads(requests[0].content) == []
    assert result.action == "updated"


async def test_an_entry_without_a_definition_is_refused_before_the_write():
    client, requests = mock_wflow({"/api/acme/storage/files/sf-1/properties/withdefinition": None})

    with pytest.raises(WflowError) as refusal:
        await storage_files.update_storage_file_properties_with_definition(
            client, "acme", "sf-1", [{"id": "pd-1", "value": "Eva"}]
        )

    assert "[0]" in str(refusal.value)
    assert "update_storage_file_properties" in str(refusal.value)
    assert requests == []


EMPTY_LIST_REFUSED = [
    ("update_storage_file_properties", "/api/acme/storage/files/sf-1/properties"),
    ("update_storage_file_properties_with_definition", "/api/acme/storage/files/sf-1/properties/withdefinition"),
]


@pytest.mark.parametrize("name,path", EMPTY_LIST_REFUSED)
async def test_an_empty_list_body_is_refused_where_it_was_never_documented(name, path):
    client, requests = mock_wflow({path: None})

    with pytest.raises(WflowError, match="empty list"):
        await getattr(storage_files, name)(client, "acme", "sf-1", [])

    assert requests == []


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("get_storage_file", {"fileId": "."}),
        ("delete_storage_file", {"fileId": ".."}),
        ("delete_storage_file_property", {"fileId": "sf-1", "propertyId": ".."}),
        ("move_storage_file", {"fileId": "..", "folderId": "fo-2"}),
    ],
)
async def test_a_run_of_dots_never_reaches_the_wire(name, arguments):
    client, requests = mock_wflow({"/api/acme/storage/files": None, "/api/acme/storage/files/sf-1": None})

    with pytest.raises(WflowError, match="run of dots"):
        await getattr(storage_files, name)(client, "acme", **arguments)

    assert requests == []


async def test_a_move_to_a_folder_wflow_does_not_know_reports_the_status():
    client, _ = mock_wflow({}, errors={"/api/acme/storage/files/sf-1/move": 404})

    with pytest.raises(WflowApiError, match="404") as failed:
        await storage_files.move_storage_file(client, "acme", "sf-1", "fo-missing")

    assert (failed.value.method, failed.value.path) == ("PUT", "/api/acme/storage/files/sf-1/move")


async def test_a_storage_download_is_the_files_bytes():
    client, requests = mock_download(b"%PDF-1.7 stored", filename="contract.pdf")

    file = await storage_files.download_storage_file(client, "acme", "sf-1")

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/api/acme/storage/files/sf-1/download"
    assert file == FileContent(filename="contract.pdf", content_type="application/pdf", content=b"%PDF-1.7 stored")


async def test_a_storage_download_over_its_limit_is_refused():
    client, _ = mock_download(b"x" * 33)

    with pytest.raises(WflowError, match="32-byte limit"):
        await storage_files.download_storage_file(client, "acme", "sf-1", max_bytes=32)


async def test_a_download_id_of_dots_never_reaches_the_wire():
    client, requests = mock_download(b"x")

    with pytest.raises(WflowError, match="run of dots"):
        await storage_files.download_storage_file(client, "acme", "..")

    assert requests == []


async def test_an_uploaded_storage_file_is_multipart_and_hands_back_its_id():
    client, requests = mock_wflow({"/api/acme/storage/files/upload": "sf-9"})

    result = await storage_files.upload_storage_file(
        client, "acme", "scan.pdf", b"%PDF-1.7", folderId="fo-1", overrideIfExists=False
    )

    sent = requests[0]
    assert sent.method == "PUT"
    assert sent.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="scan.pdf"' in sent.content
    assert b"%PDF-1.7" in sent.content
    assert sent.url.params["folderId"] == "fo-1"
    assert sent.url.params["overrideIfExists"] == "false"
    assert (result.action, result.resource, result.id) == ("created", "storage/files", "sf-9")


async def test_an_upload_wflow_answers_without_a_body_leaves_the_id_unset():
    client, _ = mock_wflow({"/api/acme/storage/files/upload": None})

    result = await storage_files.upload_storage_file(client, "acme", "scan.pdf", b"%PDF", folderId="fo-1")

    assert result.id is None


async def test_an_empty_file_is_uploaded_as_an_empty_part_rather_than_refused():
    client, requests = mock_wflow({"/api/acme/storage/files/upload": "sf-0"})

    result = await storage_files.upload_storage_file(client, "acme", "empty.txt", b"", folderId="fo-1")

    assert b'filename="empty.txt"' in requests[0].content
    assert "overrideIfExists" not in requests[0].url.params
    assert result.id == "sf-0"


def test_the_file_operations_describe_bytes_not_staging():
    for operation in (storage_files.download_storage_file, storage_files.upload_storage_file):
        doc = operation.__doc__ or ""
        for word in ("uploadId", "downloadUrl", "zipPassword", "staged", "archive format", "tool"):
            assert word not in doc, f"{operation.__name__} still says {word!r}"
        assert "Fields:" in doc
