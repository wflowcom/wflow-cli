import json

import httpx
import pytest

from tests.helpers import API_BASE, HEADERS, client_for, fake_token, mock_download, mock_response
from wflow_api.client import WflowClient
from wflow_api.errors import WflowApiError, WflowError
from wflow_api.models.common import FileContent


async def test_every_call_carries_the_callers_headers_the_bearer_and_accept():
    client, sent = mock_response(200, json={})

    await client.request("GET", "/api/acme/documents")

    for name, value in HEADERS.items():
        assert sent[0].headers[name] == value
    assert sent[0].headers["Authorization"] == "Bearer test-token"
    assert sent[0].headers["Accept"] == "application/json"
    assert str(sent[0].url) == f"{API_BASE}/api/acme/documents"


async def test_the_token_is_asked_for_on_every_request():
    asked = []

    async def token() -> str:
        asked.append(1)
        return f"t-{len(asked)}"

    sent: list[httpx.Request] = []

    def handler(request):
        sent.append(request)
        return httpx.Response(200, json={})

    client = WflowClient(token, api_base=API_BASE, headers=HEADERS, transport=httpx.MockTransport(handler))
    await client.request("GET", "/a")
    await client.request("GET", "/b")

    assert [request.headers["Authorization"] for request in sent] == ["Bearer t-1", "Bearer t-2"]


async def test_problem_details_reach_the_caller():
    client, _ = mock_response(400, json={"title": "Validation failed", "detail": "externalId must be unique"})

    with pytest.raises(WflowApiError, match="externalId must be unique") as failed:
        await client.request("PUT", "/api/acme/registers/partners")

    assert (failed.value.status, failed.value.method, failed.value.path) == (400, "PUT", "/api/acme/registers/partners")
    assert failed.value.detail == "Validation failed — externalId must be unique"


async def test_the_host_status_and_path_are_named():
    client, _ = mock_response(404, json={"title": "Not Found"})

    with pytest.raises(
        WflowApiError, match=r"wflow apitest\.wflow\.com GET /api/acme/documents returned 404\. Not Found"
    ):
        await client.request("GET", "/api/acme/documents")


async def test_an_html_error_page_does_not_mask_the_status():
    client, _ = mock_response(502, content=b"<html>bad gateway</html>", headers={"content-type": "text/html"})

    with pytest.raises(WflowApiError, match="502"):
        await client.request("GET", "/api/acme/documents")


async def test_an_error_says_nothing_about_mcp():
    client, _ = mock_response(401, json={"title": "Unauthorized"})

    with pytest.raises(WflowApiError) as failed:
        await client.request("GET", "/api/acme/documents")

    assert "reconnect" not in str(failed.value).lower() and "mcp" not in str(failed.value).lower()


async def test_an_empty_success_is_none():
    client, _ = mock_response(200, content=b"")

    assert await client.request("PUT", "/api/acme/documents/d-1/tags/x") is None


async def test_a_non_json_success_body_raises_instead_of_crashing():
    client, _ = mock_response(200, content=b"<html>not json</html>", headers={"content-type": "text/html"})

    with pytest.raises(WflowError, match="not JSON"):
        await client.request("GET", "/api/acme/documents/d-1/metadata")


async def test_an_upload_is_multipart_under_the_named_field():
    client, sent = mock_response(200, json={"id": "f-1"})

    result = await client.upload(
        "POST", "/api/acme/documents/withfiles", "a.pdf", b"%PDF", {"typeId": "t"}, "uploadedFiles"
    )

    assert result == {"id": "f-1"}
    assert sent[0].url.params["typeId"] == "t"
    assert b'name="uploadedFiles"; filename="a.pdf"' in sent[0].content
    assert b"%PDF" in sent[0].content


async def test_a_download_returns_the_bytes_and_what_wflow_said_about_them():
    client, sent = mock_download(b"%PDF-1.7", filename="invoice.pdf")

    file = await client.download("/api/acme/documents/files/f-1/download")

    assert file == FileContent(filename="invoice.pdf", content_type="application/pdf", content=b"%PDF-1.7")
    assert sent[0].headers["Authorization"] == "Bearer test-token"
    assert sent[0].headers["X-Client-Id"] == "wflowinternal"


async def test_a_download_reads_an_rfc_5987_filename():
    client, _ = mock_download(b"x", content_disposition="attachment; filename*=UTF-8''faktura-%C4%8D.pdf")

    assert (await client.download("/f")).filename == "faktura-č.pdf"


async def test_a_download_without_a_filename_is_not_an_error():
    client, _ = mock_download(b"x", filename=None)

    assert (await client.download("/f")).filename is None


async def test_a_download_can_post_a_body():
    client, sent = mock_download(b"csv")

    await client.download("/api/acme/documents/export/excel", method="POST", json={"sort": "number asc"})

    assert sent[0].method == "POST"
    assert json.loads(sent[0].content) == {"sort": "number asc"}


async def test_a_204_download_is_reported_as_no_content():
    client, _ = mock_response(204)

    with pytest.raises(WflowError, match="204"):
        await client.download("/f")


async def test_a_redirect_is_reported_rather_than_silently_empty():
    client, _ = mock_response(302, headers={"location": "https://example.com/elsewhere"})

    with pytest.raises(WflowError, match="302"):
        await client.download("/f")


async def test_a_download_error_status_is_an_api_error():
    client, _ = mock_response(404, json={"title": "Not Found"})

    with pytest.raises(WflowApiError, match="404"):
        await client.download("/f")


async def test_a_non_numeric_content_length_does_not_crash():
    client, _ = mock_response(200, content=b"hi", headers={"content-length": "not-a-number"})

    with pytest.raises(WflowError, match="Content-Length"):
        await client.download("/f")


async def test_a_declared_size_over_the_limit_is_refused_before_reading():
    client, _ = mock_download(b"x" * 11)

    with pytest.raises(WflowError, match="11 bytes, over the 10-byte limit"):
        await client.download("/f", max_bytes=10)


async def test_a_streamed_size_over_the_limit_is_refused():
    client, _ = mock_download(b"x" * (3 << 20), declare_length=False)

    with pytest.raises(WflowError, match="limit"):
        await client.download("/f", max_bytes=1 << 20)


async def test_without_a_limit_any_size_comes_through():
    client, _ = mock_download(b"x" * (3 << 20), declare_length=False)

    assert len((await client.download("/f")).content) == 3 << 20


async def test_a_rate_limit_is_an_api_error():
    client, _ = mock_response(429, json={"title": "Too Many Requests"})

    with pytest.raises(WflowApiError) as failed:
        await client.request("GET", "/api/acme/documents")

    assert failed.value.status == 429


def _unreachable(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


async def test_an_unreachable_host_on_a_request_is_a_wflow_error():
    client = client_for(_unreachable)

    with pytest.raises(
        WflowError,
        match=r"^wflow apitest\.wflow\.com GET /api/acme/documents failed: ConnectError: connection refused\.$",
    ):
        await client.request("GET", "/api/acme/documents")


async def test_a_transport_failure_without_a_message_names_only_its_type():
    def silent(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("", request=request)

    with pytest.raises(WflowError, match=r"^wflow apitest\.wflow\.com GET /f failed: ConnectError\.$"):
        await client_for(silent).request("GET", "/f")


@pytest.mark.parametrize("call", [lambda client: client.request("GET", "/f"), lambda client: client.download("/f")])
async def test_a_malformed_api_base_is_a_wflow_error(call):
    client = WflowClient(fake_token, api_base="https://api.wflow.com:abc", headers=HEADERS)

    with pytest.raises(WflowError, match=r"GET /f failed: InvalidURL: Invalid port: 'abc'\.$"):
        await call(client)


async def test_a_redirect_is_an_api_error_not_a_silent_success():
    client, _ = mock_response(301, content=b"", headers={"location": "https://elsewhere.example/x"})

    with pytest.raises(WflowApiError) as failed:
        await client.request("POST", "/api/acme/documents")

    assert (failed.value.status, failed.value.method, failed.value.path) == (301, "POST", "/api/acme/documents")


async def test_an_unreachable_host_on_an_upload_is_a_wflow_error():
    client = client_for(_unreachable)

    with pytest.raises(WflowError, match="POST /api/acme/documents/withfiles failed: ConnectError"):
        await client.upload("POST", "/api/acme/documents/withfiles", "a.pdf", b"%PDF")


async def test_an_unreachable_host_on_a_download_is_a_wflow_error():
    client = client_for(_unreachable)

    with pytest.raises(WflowError, match="GET /f failed: ConnectError"):
        await client.download("/f")


async def test_a_connection_dropped_mid_download_is_a_wflow_error():
    async def dropping():
        yield b"%PDF"
        raise httpx.RemoteProtocolError("peer closed connection")

    client = client_for(lambda request: httpx.Response(200, content=dropping()))

    with pytest.raises(WflowError, match="GET /f failed: RemoteProtocolError"):
        await client.download("/f")
