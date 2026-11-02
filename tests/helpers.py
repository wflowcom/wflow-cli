import ast
import inspect
import textwrap
from collections.abc import Callable

import httpx

from wflow_api.client import WflowClient

API_BASE = "https://apitest.wflow.com"
HEADERS = {"X-Client-Id": "wflowinternal", "X-Integration-Id": "wflow_tests", "X-Integration-Version": "0"}

ACCOUNT_BODY = {
    "id": "u-1",
    "identity": {"login": "lukas@wflow.com", "fullName": "Lukas Kosina", "language": "cs"},
    "created": "2024-03-01T09:00:00Z",
    "hasFullAccess": True,
    "roles": [{"id": "r-1", "name": "Approver", "description": "Approves documents"}],
    "teams": [{"id": "t-1", "name": "Finance", "system": False}],
    "documentTypes": [
        {"documentType": {"id": "d-1", "name": "Faktura", "kind": "IncomingInvoice"}, "permission": "OnlyAssigned"}
    ],
    "rights": ["CanApprove", "CanCreateDocument"],
}
ORGS_BODY = [{"name": "Data Test", "baseURL": "data-test.wflow.com", "subdomain": "data-test", "trialExpiration": None}]


async def fake_token() -> str:
    return "test-token"


def client_for(handler: Callable[[httpx.Request], httpx.Response]) -> WflowClient:
    return WflowClient(fake_token, api_base=API_BASE, headers=HEADERS, transport=httpx.MockTransport(handler))


def mock_wflow(
    routes: dict[str, object], status: int = 200, errors: dict[str, int] | None = None
) -> tuple[WflowClient, list[httpx.Request]]:
    """Serve a path → body table. A body of None answers 200 with no content, as wflow's writes do."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if errors and request.url.path in errors:
            return httpx.Response(errors[request.url.path], json={"title": "Rejected", "detail": request.url.path})
        if status >= 400:
            return httpx.Response(status, json={"title": "Rejected", "detail": request.url.path})
        if request.url.path in routes:
            body = routes[request.url.path]
            return httpx.Response(200) if body is None else httpx.Response(200, json=body)
        return httpx.Response(404, json={"title": "Not Found", "detail": request.url.path})

    return client_for(handler), requests


def mock_response(
    status: int, json: object = None, content: bytes | None = None, headers: dict[str, str] | None = None
) -> tuple[WflowClient, list[httpx.Request]]:
    """Answer every request with one response."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if content is not None:
            return httpx.Response(status, content=content, headers=headers or {"content-type": "application/json"})
        return httpx.Response(status, json=json, headers=headers)

    return client_for(handler), requests


async def _chunks(content: bytes, size: int = 1 << 20):
    for start in range(0, len(content), size):
        yield content[start : start + size]


def mock_download(
    content: bytes,
    content_type: str = "application/pdf",
    filename: str | None = "invoice.pdf",
    declare_length: bool = True,
    content_disposition: str | None = None,
) -> tuple[WflowClient, list[httpx.Request]]:
    """Serve one file. declare_length=False streams it without a Content-Length."""
    headers = {"content-type": content_type}
    if content_disposition is not None:
        headers["content-disposition"] = content_disposition
    elif filename is not None:
        headers["content-disposition"] = f'attachment; filename="{filename}"'
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=content if declare_length else _chunks(content), headers=headers)

    return client_for(handler), requests


def body_source(fn: Callable[..., object]) -> str:
    """An operation's body as source, its docstring dropped."""
    func = ast.parse(textwrap.dedent(inspect.getsource(inspect.unwrap(fn)))).body[0]
    body = func.body[1:] if ast.get_docstring(func) else func.body
    return "\n".join(ast.unparse(statement) for statement in body)
