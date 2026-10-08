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

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
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


async def test_a_success_without_a_token_is_refused():
    transport, _ = token_server({"token_type": "Bearer"})

    with pytest.raises(WflowError, match="access_token"):
        await ClientCredentials("c", "s", ACCOUNT, transport=transport)()


def test_both_environments_authenticate_against_the_same_authority():
    assert ENVIRONMENTS["prod"] == ("https://api.wflow.com", "https://account.wflow.com")
    assert ENVIRONMENTS["test"] == ("https://apitest.wflow.com", "https://account.wflow.com")
