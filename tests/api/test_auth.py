import asyncio
from urllib.parse import parse_qs

import httpx
import pytest

from wflow_api import auth
from wflow_api.auth import ENVIRONMENTS, ClientCredentials
from wflow_api.errors import WflowApiError, WflowError

ACCOUNT = "https://account.wflow.com"


def token_server(*bodies, status=200):
    sent: list[httpx.Request] = []
    answers = list(bodies)

    async def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        await asyncio.sleep(0)
        body = answers.pop(0) if len(answers) > 1 else answers[0]
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler), sent


async def test_the_token_request_is_the_documented_form():
    transport, sent = token_server({"access_token": "t-1", "expires_in": 3600})

    token = await ClientCredentials("acme_client", "s3cret", ACCOUNT, transport=transport)()

    assert token == "t-1"
    assert str(sent[0].url) == "https://account.wflow.com/connect/token"
    assert sent[0].headers["content-type"] == "application/x-www-form-urlencoded"
    assert parse_qs(sent[0].content.decode()) == {
        "client_id": ["acme_client"],
        "client_secret": ["s3cret"],
        "grant_type": ["client_credentials"],
        "scope": ["uccl_common_api"],
    }


async def test_a_token_is_reused_until_it_nears_expiry(monkeypatch):
    transport, sent = token_server(
        {"access_token": "t-1", "expires_in": 3600}, {"access_token": "t-2", "expires_in": 3600}
    )
    now = [1000.0]
    monkeypatch.setattr(auth.time, "monotonic", lambda: now[0])
    credentials = ClientCredentials("c", "s", ACCOUNT, transport=transport)

    assert await credentials() == "t-1"
    now[0] += 3600 - 61
    assert await credentials() == "t-1"
    now[0] += 2
    assert await credentials() == "t-2"
    assert len(sent) == 2


async def test_concurrent_callers_on_a_cold_cache_fetch_one_token():
    transport, sent = token_server({"access_token": "t-1", "expires_in": 3600})
    credentials = ClientCredentials("c", "s", ACCOUNT, transport=transport)

    tokens = await asyncio.gather(*(credentials() for _ in range(10)))

    assert set(tokens) == {"t-1"}
    assert len(sent) == 1


async def test_a_refused_client_names_the_oauth_error_and_never_the_secret():
    transport, _ = token_server({"error": "invalid_client"}, status=400)

    with pytest.raises(WflowApiError) as refused:
        await ClientCredentials("c", "s3cret-value", ACCOUNT, transport=transport)()

    message = str(refused.value)
    assert "400" in message and "invalid_client" in message and "account.wflow.com" in message
    assert "s3cret-value" not in message
    assert (refused.value.status, refused.value.method, refused.value.path) == (400, "POST", "/connect/token")


async def test_an_oauth_error_description_is_kept_whole():
    transport, _ = token_server({"error": "invalid_scope", "error_description": "scope (uccl_common_api)"}, status=400)

    with pytest.raises(WflowApiError) as refused:
        await ClientCredentials("c", "s", ACCOUNT, transport=transport)()

    assert refused.value.detail == "invalid_scope: scope (uccl_common_api)"
    assert "(invalid_scope: scope (uccl_common_api))" in str(refused.value)


async def test_an_html_error_page_surfaces_the_status():
    transport = httpx.MockTransport(lambda request: httpx.Response(502, text="<html>Bad Gateway</html>"))

    with pytest.raises(WflowApiError) as refused:
        await ClientCredentials("c", "s", ACCOUNT, transport=transport)()

    assert refused.value.status == 502
    assert refused.value.detail == ""
    assert str(refused.value) == "wflow account.wflow.com POST /connect/token returned 502."


async def test_an_unreachable_token_endpoint_raises_a_wflow_error_without_the_secret():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(WflowError) as unreachable:
        await ClientCredentials("c", "s3cret-value", ACCOUNT, transport=httpx.MockTransport(handler))()

    assert (
        str(unreachable.value)
        == "wflow account.wflow.com POST /connect/token could not be reached: ConnectError: connection refused."
    )
    assert "s3cret" not in str(unreachable.value)
    assert isinstance(unreachable.value.__cause__, httpx.ConnectError)


async def test_a_malformed_account_base_raises_a_wflow_error():
    with pytest.raises(WflowError, match=r"could not be reached: InvalidURL: Invalid port: 'abc'\.$"):
        await ClientCredentials("c", "s3cret-value", "https://account.wflow.com:abc")()


@pytest.mark.parametrize("token", [None, "", 42])
async def test_a_success_with_an_empty_or_non_text_token_is_refused(token):
    transport, _ = token_server({"access_token": token, "expires_in": 3600})

    with pytest.raises(WflowError, match="access_token"):
        await ClientCredentials("c", "s", ACCOUNT, transport=transport)()


async def test_a_success_without_a_token_is_refused():
    transport, _ = token_server({"token_type": "Bearer"})

    with pytest.raises(WflowError, match="access_token"):
        await ClientCredentials("c", "s", ACCOUNT, transport=transport)()


def test_both_environments_authenticate_against_the_same_authority():
    assert ENVIRONMENTS["prod"] == ("https://api.wflow.com", "https://account.wflow.com")
    assert ENVIRONMENTS["test"] == ("https://apitest.wflow.com", "https://account.wflow.com")
