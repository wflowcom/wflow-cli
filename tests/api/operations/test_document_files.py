import pytest

from tests.helpers import mock_download, mock_response, mock_wflow
from wflow_api.errors import WflowError
from wflow_api.models.common import FileContent
from wflow_api.operations import document_files

FILES_BODY = [
    {"id": "f-1", "name": "invoice.pdf", "main": True, "signed": False, "stamped": True},
    {"id": "f-2", "name": "annex.pdf", "main": False},
]


async def test_document_files_are_listed_typed():
    client, _ = mock_wflow({"/api/acme/documents/d-1/files": FILES_BODY})

    result = await document_files.list_document_files(client, organization="acme", documentId="d-1")

    assert [file.name for file in result] == ["invoice.pdf", "annex.pdf"]
    assert result[0].main is True


async def test_the_main_file_comes_back_as_its_own_bytes():
    client, requests = mock_download(b"%PDF-1.7 hello")

    result = await document_files.download_document_main_file(client, organization="acme", documentId="d-1")

    assert result == FileContent(filename="invoice.pdf", content_type="application/pdf", content=b"%PDF-1.7 hello")
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/api/acme/documents/d-1/files/main/download"
    assert requests[0].headers["authorization"] == "Bearer test-token"


async def test_a_document_without_a_main_file_is_a_named_204():
    client, _ = mock_response(204)

    with pytest.raises(WflowError, match="204"):
        await document_files.download_document_main_file(client, organization="acme", documentId="d-1")


async def test_one_file_comes_back_under_the_name_wflow_gave_it():
    client, requests = mock_download(b"x", filename="scan 2026.pdf")

    result = await document_files.download_document_file(client, organization="acme", fileId="f-1")

    assert result.filename == "scan 2026.pdf"
    assert requests[0].url.path == "/api/acme/documents/files/f-1/download"
    assert requests[0].headers["authorization"] == "Bearer test-token"


@pytest.mark.parametrize(
    "disposition,expected",
    [
        ({"filename": None}, None),
        ({"filename": "a;b.pdf"}, "a;b.pdf"),
        ({"content_disposition": "attachment; filename*=UTF-8''sc%C3%A1n.pdf"}, "scán.pdf"),
    ],
)
async def test_the_filename_is_read_the_way_the_rfcs_say(disposition, expected):
    client, _ = mock_download(b"x", **disposition)

    result = await document_files.download_document_file(client, organization="acme", fileId="f-1")

    assert result.filename == expected


@pytest.mark.parametrize(
    "name,arguments",
    [
        ("download_document_main_file", {"documentId": "d-1"}),
        ("download_document_file", {"fileId": "f-1"}),
    ],
)
async def test_an_oversized_file_is_refused_with_its_declared_size(name, arguments):
    client, _ = mock_download(b"x" * 33)

    with pytest.raises(WflowError, match="is 33 bytes, over the 32-byte limit"):
        await getattr(document_files, name)(client, organization="acme", **arguments, max_bytes=32)


async def test_the_cumulative_check_fires_without_a_content_length():
    client, _ = mock_download(b"x" * ((1 << 20) + 1), declare_length=False)

    with pytest.raises(WflowError, match="limit"):
        await document_files.download_document_file(client, organization="acme", fileId="f-1", max_bytes=1 << 20)


@pytest.mark.parametrize(
    "name,arguments,method,path,outcome",
    [
        (
            "delete_document_file",
            {"fileId": "f-1"},
            "DELETE",
            "/api/acme/documents/files/f-1",
            ("deleted", "documents/files"),
        ),
        (
            "stamp_document_file",
            {"documentId": "d-1", "fileId": "f-1"},
            "PUT",
            "/api/acme/documents/d-1/files/f-1/stamp",
            ("stamped", "documents/files"),
        ),
    ],
)
async def test_each_bodiless_write_builds_its_request(name, arguments, method, path, outcome):
    client, requests = mock_wflow({path: None})

    result = await getattr(document_files, name)(client, organization="acme", **arguments)

    assert (requests[0].method, requests[0].url.path) == (method, path)
    assert not requests[0].content
    assert (result.action, result.resource) == outcome


async def test_an_upload_sends_multipart_with_the_bytes():
    client, requests = mock_wflow({"/api/acme/documents/d-1/files/upload": None})

    result = await document_files.upload_document_file(
        client, organization="acme", documentId="d-1", filename="scan.pdf", content=b"%PDF-1.7", main=True
    )

    sent = requests[0]
    assert sent.method == "PUT"
    assert sent.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"; filename="scan.pdf"' in sent.content
    assert b"%PDF-1.7" in sent.content
    assert sent.url.params["main"] == "true"
    assert (result.action, result.resource, result.id) == ("created", "documents/files", None)


async def test_an_uploaded_document_file_hands_back_its_id():
    client, _ = mock_wflow({"/api/acme/documents/d-1/files/upload": "f-9"})

    result = await document_files.upload_document_file(
        client, organization="acme", documentId="d-1", filename="annex.pdf", content=b"%PDF-1.7"
    )

    assert (result.action, result.id) == ("created", "f-9")


async def test_a_non_ascii_filename_reaches_wflow_as_utf8():
    client, requests = mock_wflow({"/api/acme/documents/d-1/files/upload": None})

    await document_files.upload_document_file(
        client, organization="acme", documentId="d-1", filename="faktura-č.pdf", content=b"%PDF-1.7"
    )

    assert 'filename="faktura-č.pdf"'.encode() in requests[0].content


async def test_a_zero_byte_upload_is_sent_and_hands_back_its_id():
    client, requests = mock_wflow({"/api/acme/documents/d-1/files/upload": "f-0"})

    result = await document_files.upload_document_file(
        client, organization="acme", documentId="d-1", filename="blank.pdf", content=b""
    )

    assert len(requests) == 1
    assert b'name="file"; filename="blank.pdf"' in requests[0].content
    assert (result.action, result.id) == ("created", "f-0")
