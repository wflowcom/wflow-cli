import json
from datetime import UTC, datetime

import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models.requests import DocumentUpdate
from wflow_api.operations import document_files, documents

DOCUMENTS_BODY = {
    "items": [
        {"id": "d-1", "number": "2026001", "partnerName": "Noname Ltd.", "totalAmount": 12100.0, "currency": "CZK"},
        {"id": "d-2", "number": "2026002", "partnerName": "Other s.r.o."},
    ],
    "totalItems": 57,
    "pageSize": 2,
    "page": 0,
}
DOCUMENT_BODY = {
    "id": "d-1",
    "number": "2026001",
    "totalAmount": 12100.0,
    "currency": "CZK",
    "approvalStatus": "Approved",
    "lines": [{"description": "Consulting", "totalAmount": 10000.0}],
}
DOCUMENT_TYPES_BODY = {
    "items": [{"id": "dt-1", "name": "Faktura"}, {"id": "dt-2", "name": "Contract"}],
    "totalItems": 5,
    "pageSize": 2,
    "page": 0,
}


def test_a_document_update_accepts_a_partial_record():
    update = DocumentUpdate.model_validate({"number": "2026001", "totalAmount": "12100.0"})

    assert update.number == "2026001"
    assert update.totalAmount == 12100.0


def test_an_unset_field_is_dropped_on_serialisation():
    payload = DocumentUpdate.model_validate({"number": "2026001", "issueDate": "2026-01-15T00:00:00Z"}).model_dump(
        exclude_none=True
    )

    assert payload == {"number": "2026001", "issueDate": datetime(2026, 1, 15, tzinfo=UTC)}


async def test_documents_come_back_with_their_paging():
    client, _ = mock_wflow({"/api/acme/documents": DOCUMENTS_BODY})

    result = await documents.list_documents(client, organization="acme")

    assert [document.number for document in result.items] == ["2026001", "2026002"]
    assert result.totalItems == 57


async def test_a_null_items_page_comes_back_empty_not_an_error():
    client, _ = mock_wflow({"/api/acme/documents": {"items": None, "totalItems": 0}})

    result = await documents.list_documents(client, organization="acme")

    assert result.items == []
    assert result.totalItems == 0


async def test_list_documents_forwards_its_filter():
    client, requests = mock_wflow({"/api/acme/documents": DOCUMENTS_BODY})

    await documents.list_documents(client, organization="acme", query="totalAmount > 1000", pageSize=20)

    assert requests[0].url.params["query"] == "totalAmount > 1000"
    assert requests[0].url.params["pageSize"] == "20"
    assert "search" not in requests[0].url.params


async def test_one_document_carries_its_lines():
    client, _ = mock_wflow({"/api/acme/documents/d-1": DOCUMENT_BODY})

    result = await documents.get_document(client, organization="acme", documentId="d-1")

    assert result.lines[0].description == "Consulting"
    assert result.approvalStatus == "Approved"


@pytest.mark.parametrize(
    "name,path,body,check",
    [
        (
            "list_document_events",
            "/api/acme/documents/d-1/events",
            [{"id": "e-1", "type": "Create", "info": "by Jan"}],
            lambda d: d[0].type == "Create" and "identity" in type(d[0]).model_fields,
        ),
        (
            "list_document_comments",
            "/api/acme/documents/d-1/comments",
            [{"id": "c-1", "text": "Looks wrong", "markdown": "Looks wrong"}],
            lambda d: d[0].text == "Looks wrong" and "markdown" in type(d[0]).model_fields,
        ),
        (
            "list_document_links",
            "/api/acme/documents/d-1/links",
            [{"id": "d-9", "number": "2026009"}],
            lambda d: d[0].number == "2026009" and "totalAmount" in type(d[0]).model_fields,
        ),
        (
            "get_document_rights",
            "/api/acme/documents/d-1/rights",
            [{"id": "t-1", "name": "Finance"}],
            lambda d: d[0].name == "Finance" and "system" in type(d[0]).model_fields,
        ),
    ],
)
async def test_the_document_sub_resources(name, path, body, check):
    client, _ = mock_wflow({path: body})

    result = await getattr(documents, name)(client, organization="acme", documentId="d-1")

    assert check(result)


async def test_get_document_type_sends_typeid_as_a_query_argument():
    client, requests = mock_wflow({"/api/acme/documents/types/typeid:guid": {"id": "t-1", "name": "Faktura"}})

    result = await documents.get_document_type(client, organization="acme", typeId="t-1")

    assert requests[0].url.params["typeId"] == "t-1"
    assert result.name == "Faktura"


@pytest.mark.parametrize(
    "name,path,ids",
    [
        ("list_documents_to_export", "/api/acme/documents/toexport", ["d-1", "d-2"]),
        ("list_documents_to_extract", "/api/acme/documents/toextract", ["d-3", "d-4"]),
    ],
)
async def test_documents_waiting_for_work_are_a_list_of_ids(name, path, ids):
    client, _ = mock_wflow({path: ids})

    assert await getattr(documents, name)(client, organization="acme") == ids


async def test_documents_to_export_forwards_its_filter():
    client, requests = mock_wflow({"/api/acme/documents/toexport": []})

    await documents.list_documents_to_export(client, organization="acme", typeId="dt-1", exclude=True)

    assert requests[0].url.params["typeId"] == "dt-1"
    assert requests[0].url.params["exclude"] == "true"


@pytest.mark.parametrize(
    "name,path",
    [
        ("list_documents_to_export", "/api/acme/documents/toexport"),
        ("list_documents_to_extract", "/api/acme/documents/toextract"),
    ],
)
async def test_a_wrong_outer_shape_raises_instead_of_silently_iterating_keys(name, path):
    client, _ = mock_wflow({path: {"items": ["should not be reached"]}})

    with pytest.raises(WflowError, match="not an array"):
        await getattr(documents, name)(client, organization="acme")


async def test_document_types_come_back_with_their_paging():
    client, _ = mock_wflow({"/api/acme/documents/types": DOCUMENT_TYPES_BODY})

    result = await documents.list_document_types(client, organization="acme")

    assert [document_type.name for document_type in result.items] == ["Faktura", "Contract"]
    assert result.totalItems == 5


async def test_list_document_types_forwards_its_filter():
    client, requests = mock_wflow({"/api/acme/documents/types": DOCUMENT_TYPES_BODY})

    await documents.list_document_types(client, organization="acme", search="Faktura", pageSize=10)

    assert requests[0].url.params["search"] == "Faktura"
    assert requests[0].url.params["pageSize"] == "10"


async def test_metadata_passes_through_untyped():
    client, _ = mock_wflow({"/api/acme/documents/d-1/metadata": {"anything": {"nested": 1}}})

    result = await documents.get_document_metadata(client, organization="acme", documentId="d-1")

    assert result["anything"]["nested"] == 1


async def test_metadata_decodes_a_double_encoded_json_string():
    client, _ = mock_wflow({"/api/acme/documents/d-1/metadata": json.dumps({"anything": {"nested": 1}})})

    result = await documents.get_document_metadata(client, organization="acme", documentId="d-1")

    assert result["anything"]["nested"] == 1


async def test_metadata_that_is_not_json_is_wrapped_rather_than_lost():
    client, _ = mock_wflow({"/api/acme/documents/d-1/metadata": "plain text"})

    result = await documents.get_document_metadata(client, organization="acme", documentId="d-1")

    assert result == {"metadata": "plain text"}


@pytest.mark.parametrize(
    "name,arguments,path,resource",
    [
        ("delete_document", {"documentId": "d-1"}, "/api/acme/documents/d-1", "documents"),
        (
            "unlink_document",
            {"documentId": "d-1", "linkedDocumentId": "d-2"},
            "/api/acme/documents/d-1/links/d-2",
            "documents/links",
        ),
    ],
)
async def test_each_delete_hits_its_own_path(name, arguments, path, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(documents, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == ("DELETE", path)
    assert (result.action, result.resource) == ("deleted", resource)


async def test_delete_document_type_sends_typeid_as_a_query_argument():
    path = "/api/acme/documents/types/typeid:guid"
    client, requests = mock_wflow({path: None})

    result = await documents.delete_document_type(client, organization="acme", typeId="dt-1")

    assert (requests[0].method, requests[0].url.path) == ("DELETE", path)
    assert requests[0].url.params["typeId"] == "dt-1"
    assert (result.action, result.resource) == ("deleted", "documents/types")


@pytest.mark.parametrize(
    "module,name,arguments,neighbour,message,raw",
    [
        (
            document_files,
            "delete_document_file",
            {"fileId": "../d-1"},
            "/api/acme/documents/d-1",
            "404",
            b"/api/acme/documents/files/..%2Fd-1",
        ),
        (
            documents,
            "get_document",
            {"documentId": "d-1?x=1"},
            "/api/acme/documents/d-1",
            "404",
            b"/api/acme/documents/d-1%3Fx%3D1",
        ),
        (
            documents,
            "unlink_document",
            {"documentId": "d-1", "linkedDocumentId": ".."},
            "/api/acme/documents/d-1",
            "run of dots",
            None,
        ),
        (documents, "get_document", {"documentId": "."}, "/api/acme", "run of dots", None),
    ],
)
async def test_an_id_carrying_a_delimiter_cannot_address_a_neighbour(module, name, arguments, neighbour, message, raw):
    client, requests = mock_wflow({neighbour: None})

    with pytest.raises(WflowError, match=message):
        await getattr(module, name)(client, organization="acme", **arguments)

    if raw is None:
        assert requests == []
    else:
        assert requests[0].url.raw_path == raw


@pytest.mark.parametrize(
    "name,arguments,method,path,params,outcome",
    [
        (
            "lock_document",
            {"documentId": "d-1", "value": True},
            "PUT",
            "/api/acme/documents/d-1/lock/true",
            {},
            ("locked", "documents/lock"),
        ),
        (
            "lock_document",
            {"documentId": "d-1", "value": False},
            "PUT",
            "/api/acme/documents/d-1/lock/false",
            {},
            ("unlocked", "documents/lock"),
        ),
        (
            "link_document",
            {"documentId": "d-1", "linkedDocumentId": "d-2"},
            "PUT",
            "/api/acme/documents/d-1/links/d-2",
            {},
            ("linked", "documents/links"),
        ),
        (
            "create_document_task",
            {"documentId": "d-1", "type": "Extract"},
            "POST",
            "/api/acme/documents/d-1/task/Extract",
            {},
            ("created", "documents/task"),
        ),
        (
            "set_document_task_processed",
            {"documentId": "d-1", "taskType": "Extract", "success": True},
            "PUT",
            "/api/acme/documents/d-1/task/Extract/processed",
            {"success": "true"},
            ("processed", "documents/task"),
        ),
    ],
)
async def test_each_parameter_write_builds_its_request(name, arguments, method, path, params, outcome):
    client, requests = mock_wflow({path: None})

    result = await getattr(documents, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == (method, path)
    assert not requests[0].content
    assert (result.action, result.resource) == outcome
    for key, value in params.items():
        assert requests[0].url.params[key] == value


@pytest.mark.parametrize(
    "name,arguments,path,body,response,outcome",
    [
        (
            "update_document",
            {"document": {"number": "2026001"}},
            "/api/acme/documents",
            {"number": "2026001"},
            "new-id",
            ("updated", "documents"),
        ),
        (
            "update_document_payments",
            {"documentId": "d-1", "payments": [{"amount": 1210.0}]},
            "/api/acme/documents/d-1/payments",
            [{"amount": 1210.0}],
            None,
            ("updated", "documents/payments"),
        ),
        (
            "update_document_type",
            {"documentType": {"name": "Incoming invoice"}},
            "/api/acme/documents/types",
            {"name": "Incoming invoice"},
            "new-id",
            ("updated", "documents/types"),
        ),
        (
            "set_document_rights",
            {"documentId": "d-1", "teams": [{"id": "t-1"}]},
            "/api/acme/documents/d-1/rights",
            [{"id": "t-1"}],
            None,
            ("updated", "documents/rights"),
        ),
    ],
)
async def test_each_body_write_sends_its_own_payload(name, arguments, path, body, response, outcome):
    client, requests = mock_wflow({path: response})

    result = await getattr(documents, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == ("PUT", path)
    assert json.loads(requests[0].content) == body
    assert (result.action, result.resource, result.id) == (*outcome, response)


async def test_update_document_forwards_its_query_flags():
    client, requests = mock_wflow({"/api/acme/documents": "d-new"})

    await documents.update_document(
        client, organization="acme", document={"number": "1"}, externalId="ERP-9", ignoreLock=True, setAsFilled=True
    )

    assert requests[0].url.params["externalId"] == "ERP-9"
    assert requests[0].url.params["ignoreLock"] == "true"
    assert requests[0].url.params["setAsFilled"] == "true"


async def test_a_date_in_a_body_leaves_as_a_string_rather_than_raising():
    client, requests = mock_wflow({"/api/acme/documents": "d-new"})

    await documents.update_document(
        client, organization="acme", document={"number": "2026001", "issueDate": "2026-01-15T00:00:00Z"}
    )

    assert json.loads(requests[0].content) == {"number": "2026001", "issueDate": "2026-01-15T00:00:00Z"}


async def test_metadata_travels_as_a_json_string_with_a_content_type():
    client, requests = mock_wflow({"/api/acme/documents/d-1/metadata": None})

    result = await documents.update_document_metadata(
        client, organization="acme", documentId="d-1", metadata='{"vs": "2026001"}'
    )

    assert requests[0].method == "PUT"
    assert json.loads(requests[0].content) == '{"vs": "2026001"}'
    assert requests[0].headers["content-type"] == "application/json"
    assert (result.action, result.resource) == ("updated", "documents/metadata")


@pytest.mark.parametrize(
    "name,arguments,path,message",
    [
        ("update_document", {"document": {"nummber": "2026001"}}, "/api/acme/documents", "nummber"),
        (
            "update_document",
            {"document": {"lines": [{"quantity": 1.0}, {"quantitiy": 2.0}]}},
            "/api/acme/documents",
            r"lines\[1\]\.quantitiy",
        ),
        (
            "update_document_payments",
            {"documentId": "d-1", "payments": [{"amount": 1.0}, {"amont": 2.0}]},
            "/api/acme/documents/d-1/payments",
            r"\[1\]\.amont",
        ),
    ],
)
async def test_a_misspelt_field_is_refused_before_the_write(name, arguments, path, message):
    client, requests = mock_wflow({path: None})

    with pytest.raises(WflowError, match=message):
        await getattr(documents, name)(client, organization="acme", **arguments)

    assert requests == []


async def test_empty_rights_are_sent_because_they_mean_no_team():
    client, requests = mock_wflow({"/api/acme/documents/d-1/rights": None})

    result = await documents.set_document_rights(client, organization="acme", documentId="d-1", teams=[])

    assert json.loads(requests[0].content) == []
    assert result.action == "updated"


async def test_empty_payments_are_refused():
    client, requests = mock_wflow({"/api/acme/documents/d-1/payments": None})

    with pytest.raises(WflowError, match="empty list"):
        await documents.update_document_payments(client, organization="acme", documentId="d-1", payments=[])

    assert requests == []


async def test_rights_read_from_wflow_can_be_written_straight_back():
    stored = [
        {"id": "t-1", "name": "Finance", "description": "Invoice approvers", "system": False},
        {"id": "t-2", "name": "Everyone", "description": None, "system": True},
    ]
    client, requests = mock_wflow({"/api/acme/documents/d-1/rights": stored})

    read = await documents.get_document_rights(client, organization="acme", documentId="d-1")
    kept = [team.model_dump(exclude_none=True) for team in read if team.id != "t-2"]
    result = await documents.set_document_rights(client, organization="acme", documentId="d-1", teams=kept)

    assert requests[1].method == "PUT"
    assert json.loads(requests[1].content) == [
        {"id": "t-1", "name": "Finance", "description": "Invoice approvers", "system": False}
    ]
    assert result.action == "updated"


async def test_a_document_wflow_does_not_know_is_an_api_error_naming_the_path():
    client, _ = mock_wflow({}, status=404)

    with pytest.raises(WflowApiError, match="/api/acme/documents/d-404") as failed:
        await documents.get_document(client, organization="acme", documentId="d-404")

    assert failed.value.status == 404
