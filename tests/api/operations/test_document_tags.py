import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowError
from wflow_api.operations import document_tags


async def test_one_documents_tags_are_a_bare_array():
    client, requests = mock_wflow({"/api/acme/documents/d-1/tags": ["urgent", "q1"]})

    result = await document_tags.get_document_tags(client, organization="acme", documentId="d-1")

    assert result == ["urgent", "q1"]
    assert requests[0].method == "GET"


async def test_every_tag_in_the_workspace_is_listed():
    client, _ = mock_wflow({"/api/acme/documents/tags": ["urgent", "q1", "reviewed"]})

    assert await document_tags.list_document_tags(client, organization="acme") == ["urgent", "q1", "reviewed"]


@pytest.mark.parametrize(
    "name,arguments,path",
    [
        ("get_document_tags", {"documentId": "d-1"}, "/api/acme/documents/d-1/tags"),
        ("list_document_tags", {}, "/api/acme/documents/tags"),
    ],
)
async def test_a_wrong_outer_shape_raises_instead_of_silently_iterating_keys(name, arguments, path):
    client, _ = mock_wflow({path: {"items": ["should not be reached"]}})

    with pytest.raises(WflowError, match="not an array"):
        await getattr(document_tags, name)(client, organization="acme", **arguments)


@pytest.mark.parametrize(
    "name,method,outcome",
    [
        ("add_document_tag", "PUT", ("added", "documents/tags")),
        ("delete_document_tag", "DELETE", ("deleted", "documents/tags")),
    ],
)
async def test_a_tag_is_added_and_deleted_on_its_own_path(name, method, outcome):
    client, requests = mock_wflow({"/api/acme/documents/d-1/tags/urgent": None})

    result = await getattr(document_tags, name)(client, organization="acme", documentId="d-1", tag="urgent")

    assert (requests[0].method, requests[0].url.path) == (method, "/api/acme/documents/d-1/tags/urgent")
    assert not requests[0].content
    assert (result.action, result.resource) == outcome


@pytest.mark.parametrize(
    "name,tag,raw,action",
    [
        ("add_document_tag", "faktura#2026", b"/api/acme/documents/d-1/tags/faktura%232026", "added"),
        ("delete_document_tag", "a#b", b"/api/acme/documents/d-1/tags/a%23b", "deleted"),
    ],
)
async def test_a_tag_with_a_url_delimiter_is_encoded_rather_than_obeyed(name, tag, raw, action):
    client, requests = mock_wflow({f"/api/acme/documents/d-1/tags/{tag}": None})

    result = await getattr(document_tags, name)(client, organization="acme", documentId="d-1", tag=tag)

    assert requests[0].url.raw_path == raw
    assert result.action == action


async def test_a_tag_of_nothing_but_dots_never_leaves():
    client, requests = mock_wflow({"/api/acme/documents/d-1": None})

    with pytest.raises(WflowError, match="run of dots"):
        await document_tags.delete_document_tag(client, organization="acme", documentId="d-1", tag="..")

    assert requests == []
