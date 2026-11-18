import base64

import pytest

from tests.helpers import mock_wflow
from wflow_api.errors import WflowError
from wflow_api.models.common import FileContent
from wflow_api.operations import peppol

MESSAGES_BODY = {
    "items": [{"id": "m-1", "status": "Delivered", "direction": "Incoming", "document": {"id": "d-1"}}],
    "totalItems": 41,
    "pageSize": 1,
    "page": 0,
}


async def test_peppol_messages_come_back_with_their_paging():
    client, _ = mock_wflow({"/api/acme/peppol/messages": MESSAGES_BODY})

    result = await peppol.list_peppol_messages(client, organization="acme")

    assert result.items[0].direction == "Incoming" and result.items[0].document.id == "d-1"
    assert result.totalItems == 41


async def test_list_peppol_messages_forwards_all_five_paging_arguments():
    client, requests = mock_wflow({"/api/acme/peppol/messages": MESSAGES_BODY})

    await peppol.list_peppol_messages(
        client,
        organization="acme",
        search="Acme",
        sort="createdAt desc",
        query='document.id = "d-1"',
        pageSize=100,
        page=2,
    )

    assert dict(requests[0].url.params) == {
        "search": "Acme",
        "sort": "createdAt desc",
        "query": 'document.id = "d-1"',
        "pageSize": "100",
        "page": "2",
    }


async def test_a_message_detail_carries_its_document_and_attachment_names():
    body = {
        "message": {"id": "m-1", "direction": "Incoming"},
        "document": {"id": "d-1", "number": "F1"},
        "attachments": [{"name": "peppol-document.xml", "contentType": "application/xml"}],
        "metadata": {"documentFormat": "UBL"},
    }
    client, requests = mock_wflow({"/api/acme/peppol/messages/m-1/detail": body})

    result = await peppol.get_peppol_message_detail(client, organization="acme", id="m-1")

    assert result.document.number == "F1" and result.attachments[0].name == "peppol-document.xml"
    assert requests[0].method == "GET"


async def test_an_attachment_comes_back_as_its_decoded_bytes():
    body = {
        "name": "peppol-document.xml",
        "contentType": "application/xml",
        "content": base64.b64encode(b"<Invoice/>").decode(),
    }
    client, requests = mock_wflow({"/api/acme/peppol/messages/m-1/attachment": body})

    result = await peppol.download_peppol_message_attachment(
        client, organization="acme", id="m-1", name="peppol-document.xml"
    )

    assert result == FileContent(filename="peppol-document.xml", content_type="application/xml", content=b"<Invoice/>")
    assert requests[0].url.params["name"] == "peppol-document.xml"


async def test_an_attachment_over_the_limit_is_refused():
    body = {"name": "a.pdf", "content": base64.b64encode(b"12345").decode()}
    client, _ = mock_wflow({"/api/acme/peppol/messages/m-1/attachment": body})

    with pytest.raises(WflowError, match="is 5 bytes, over the 4-byte limit set for this download"):
        await peppol.download_peppol_message_attachment(
            client, organization="acme", id="m-1", name="a.pdf", max_bytes=4
        )


@pytest.mark.parametrize("content,message", [(None, "no content"), ("not base64!", "base64")])
async def test_an_unusable_attachment_body_is_an_error_not_an_empty_file(content, message):
    client, _ = mock_wflow({"/api/acme/peppol/messages/m-1/attachment": {"name": "a.pdf", "content": content}})

    with pytest.raises(WflowError, match=message) as raised:
        await peppol.download_peppol_message_attachment(client, organization="acme", id="m-1", name="a.pdf")

    assert "'a.pdf'" in str(raised.value)
