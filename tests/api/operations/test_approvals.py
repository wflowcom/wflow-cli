import json

import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowError
from wflow_api.models.admin import ApprovalsTemplateFull
from wflow_api.operations import approvals

APPROVAL_PROCESS = {"pathName": "Over 10k", "items": [{"level": 1, "status": "Approved"}]}


def test_an_approval_template_carries_its_steps():
    template = ApprovalsTemplateFull.model_validate(
        {"id": "at-1", "name": "Over 10k", "teams": [{"teamId": "t-1", "level": 1}]}
    )

    assert (template.name, template.teams[0].level) == ("Over 10k", 1)


async def test_a_documents_approval_process_names_its_path():
    client, _ = mock_wflow({"/api/acme/documents/d-1/approvals": APPROVAL_PROCESS})

    result = await approvals.get_document_approvals(client, organization="acme", documentId="d-1")

    assert result.pathName == "Over 10k"
    assert result.items[0].level == 1


async def test_a_storage_files_approval_process_has_the_same_shape():
    client, requests = mock_wflow({"/api/acme/storage/files/sf-1/approvals": APPROVAL_PROCESS})

    result = await approvals.get_storage_file_approvals(client, organization="acme", fileId="sf-1")

    assert requests[0].url.path == "/api/acme/storage/files/sf-1/approvals"
    assert result.pathName == "Over 10k"


async def test_approval_templates_come_back_paged_with_their_filter_forwarded():
    client, requests = mock_wflow(
        {"/api/acme/approvalstemplates": {"items": [{"id": "at-1", "name": "Over 10k"}], "totalItems": 1}}
    )

    result = await approvals.list_approval_templates(client, organization="acme", search="10k", pageSize=5)

    assert result.items[0].name == "Over 10k"
    assert result.totalItems == 1
    assert requests[0].url.params["search"] == "10k"
    assert requests[0].url.params["pageSize"] == "5"
    assert "sort" not in requests[0].url.params


async def test_one_approval_template_is_read_by_its_template_id():
    client, requests = mock_wflow({"/api/acme/approvalstemplates/at-1": {"id": "at-1", "name": "Over 10k"}})

    result = await approvals.get_approval_template(client, organization="acme", templateId="at-1")

    assert requests[0].url.path == "/api/acme/approvalstemplates/at-1"
    assert result.name == "Over 10k"


@pytest.mark.parametrize(
    "name,arguments,path,resource",
    [
        ("delete_approval_template", {"templateId": "at-1"}, "/api/acme/approvalstemplates/at-1", "approvalstemplates"),
        (
            "delete_document_approval_path",
            {"documentId": "d-1"},
            "/api/acme/documents/d-1/approvals",
            "documents/approvals",
        ),
        (
            "delete_storage_file_approval_path",
            {"fileId": "sf-1"},
            "/api/acme/storage/files/sf-1/approvals",
            "storage/files/approvals",
        ),
    ],
)
async def test_each_delete_hits_its_own_path(name, arguments, path, resource):
    client, requests = mock_wflow({path: None})

    result = await getattr(approvals, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == ("DELETE", path)
    assert (result.action, result.resource) == ("deleted", resource)


async def test_a_storage_file_is_put_through_a_template_by_path_alone():
    client, requests = mock_wflow({"/api/acme/storage/files/sf-1/approvals/set/at-1": None})

    result = await approvals.set_storage_file_approval_path(
        client, organization="acme", fileId="sf-1", templateId="at-1"
    )

    assert requests[0].method == "PUT"
    assert not requests[0].content
    assert (result.action, result.resource) == ("set", "storage/files/approvals")


async def test_a_template_write_sends_only_the_fields_given_and_returns_its_id():
    client, requests = mock_wflow({"/api/acme/approvalstemplates": "at-new"})

    result = await approvals.update_approval_template(client, organization="acme", template={"name": "Two levels"})

    assert requests[0].method == "PUT"
    assert json.loads(requests[0].content) == {"name": "Two levels"}
    assert (result.action, result.resource, result.id) == ("updated", "approvalstemplates", "at-new")


async def test_a_document_approval_path_with_teams_sends_them():
    client, requests = mock_wflow({"/api/acme/documents/d-1/approvals/set/at-1": None})

    result = await approvals.set_document_approval_path(
        client,
        organization="acme",
        documentId="d-1",
        templateId="at-1",
        teams={"teams": [{"teamId": "t-1", "level": 1}]},
    )

    assert requests[0].method == "PUT"
    assert json.loads(requests[0].content) == {"teams": [{"teamId": "t-1", "level": 1}]}
    assert (result.action, result.resource, result.id) == ("set", "documents/approvals", None)


async def test_an_approval_path_set_without_teams_sends_no_body_at_all():
    client, requests = mock_wflow({"/api/acme/documents/d-1/approvals/set/at-1": None})

    result = await approvals.set_document_approval_path(
        client, organization="acme", documentId="d-1", templateId="at-1"
    )

    assert requests[0].content == b""
    assert "content-type" not in requests[0].headers
    assert result.action == "set"


async def test_a_misspelt_template_field_is_refused_before_the_write():
    client, requests = mock_wflow({"/api/acme/approvalstemplates": "at-new"})

    with pytest.raises(WflowError, match="nmae"):
        await approvals.update_approval_template(client, organization="acme", template={"nmae": "Two levels"})

    assert requests == []
