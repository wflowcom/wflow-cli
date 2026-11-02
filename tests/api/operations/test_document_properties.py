import json

import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowError
from wflow_api.operations import document_properties

DEFINITION_BODY = {
    "id": "pd-1",
    "name": "Approved budget",
    "type": "Number",
    "order": 1,
    "show": True,
    "editable": True,
    "kinds": ["IncomingInvoice"],
}


async def test_property_definitions_are_listed():
    client, _ = mock_wflow({"/api/acme/documents/properties/definitions": [DEFINITION_BODY]})

    result = await document_properties.list_document_property_definitions(client, organization="acme")

    assert result[0].name == "Approved budget"
    assert "value" not in type(result[0]).model_fields


async def test_one_definition_is_fetched_by_id():
    client, requests = mock_wflow({"/api/acme/documents/properties/definition/pd-1": DEFINITION_BODY})

    result = await document_properties.get_document_property_definition(client, organization="acme", id="pd-1")

    assert requests[0].url.path == "/api/acme/documents/properties/definition/pd-1"
    assert result.type == "Number"
    assert "value" not in type(result).model_fields


async def test_document_properties_carry_their_values():
    client, _ = mock_wflow({"/api/acme/documents/d-1/properties": [DEFINITION_BODY | {"value": 42000}]})

    result = await document_properties.get_document_properties(client, organization="acme", documentId="d-1")

    assert result[0].value == 42000
    assert "value" in type(result[0]).model_fields


@pytest.mark.parametrize(
    "name,arguments,path,resource",
    [
        (
            "delete_document_property",
            {"documentId": "d-1", "propertyId": "p-1"},
            "/api/acme/documents/d-1/properties/p-1",
            "documents/properties",
        ),
        (
            "delete_document_property_definition",
            {"id": "pd-1"},
            "/api/acme/documents/properties/definition/pd-1",
            "documents/properties/definition",
        ),
    ],
)
async def test_each_delete_hits_its_own_path(name, arguments, path, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(document_properties, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == ("DELETE", path)
    assert (result.action, result.resource) == ("deleted", resource)


@pytest.mark.parametrize(
    "name,arguments,path,body,resource",
    [
        (
            "update_document_properties",
            {"documentId": "d-1", "properties": [{"id": "pd-1", "value": "Jan"}]},
            "/api/acme/documents/d-1/properties",
            [{"id": "pd-1", "value": "Jan"}],
            "documents/properties",
        ),
        (
            "update_document_properties_with_definition",
            {"documentId": "d-1", "properties": [{"name": "Signed by", "type": "Text", "value": "Jan"}]},
            "/api/acme/documents/d-1/properties/withdefinition",
            [{"name": "Signed by", "type": "Text", "value": "Jan"}],
            "documents/properties/withdefinition",
        ),
        (
            "update_document_property_definition",
            {"definition": {"name": "Signed by", "type": "Text"}},
            "/api/acme/documents/properties/definition",
            {"name": "Signed by", "type": "Text"},
            "documents/properties/definition",
        ),
    ],
)
async def test_each_body_write_sends_its_own_payload(name, arguments, path, body, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(document_properties, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == ("PUT", path)
    assert json.loads(requests[0].content) == body
    assert (result.action, result.resource, result.id) == ("updated", resource, None)


async def test_add_only_reaches_the_wire_under_the_name_the_spec_declares():
    client, requests = mock_wflow({"/api/acme/documents/d-1/properties/withdefinition": None})

    await document_properties.update_document_properties_with_definition(
        client,
        organization="acme",
        documentId="d-1",
        properties=[{"name": "Signed by", "type": "Text", "value": "Jan"}],
        addOnly=False,
    )

    assert requests[0].url.params["addOnly"] == "false"


async def test_an_entry_without_a_definition_is_refused_before_the_write():
    client, requests = mock_wflow({"/api/acme/documents/d-1/properties/withdefinition": None})

    with pytest.raises(WflowError) as refusal:
        await document_properties.update_document_properties_with_definition(
            client,
            organization="acme",
            documentId="d-1",
            properties=[{"name": "Signed by", "type": "Text", "value": "Jan"}, {"id": "pd-1", "value": "Eva"}],
        )

    assert "[1]" in str(refusal.value)
    assert "update_document_properties" in str(refusal.value)
    assert requests == []


@pytest.mark.parametrize(
    "name,path",
    [
        ("update_document_properties", "/api/acme/documents/d-1/properties"),
        ("update_document_properties_with_definition", "/api/acme/documents/d-1/properties/withdefinition"),
    ],
)
async def test_an_empty_list_body_is_refused(name, path):
    client, requests = mock_wflow({path: None})

    with pytest.raises(WflowError, match="empty list"):
        await getattr(document_properties, name)(client, organization="acme", documentId="d-1", properties=[])

    assert requests == []
