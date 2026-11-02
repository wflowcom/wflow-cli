"""Machine-to-machine sign-in: a client_credentials token, fetched once and reused until it nears expiry."""

import asyncio
import time
from urllib.parse import urlsplit

import httpx

from wflow_api.errors import WflowApiError, WflowError

ENVIRONMENTS = {
    "prod": ("https://api.wflow.com", "https://account.wflow.com"),
    "test": ("https://apitest.wflow.com", "https://account.wflow.com"),
}
TOKEN_PATH = "/connect/token"
REFRESH_MARGIN_SECONDS = 60


def _oauth_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return ""
    if not isinstance(body, dict) or not body.get("error"):
        return ""
    described = f": {body['error_description']}" if body.get("error_description") else ""
    return f"{body['error']}{described}"


class ClientCredentials:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        account_base: str,
        scope: str = "uccl_common_api",
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._form = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": scope,
        }
        self._account_base = account_base.rstrip("/")
        self._host = urlsplit(self._account_base).netloc or self._account_base
        self._transport = transport
        self._token: str | None = None
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    async def __call__(self) -> str:
        async with self._lock:
            if self._token is None or time.monotonic() >= self._expires_at:
                self._token, self._expires_at = await self._fetch()
            return self._token

    async def _fetch(self) -> tuple[str, float]:
        try:
            async with httpx.AsyncClient(base_url=self._account_base, transport=self._transport, timeout=30) as client:
                response = await client.post(TOKEN_PATH, data=self._form)
        except (httpx.HTTPError, httpx.InvalidURL) as error:
            reason = f"{type(error).__name__}{f': {error}' if str(error) else ''}"
            raise WflowError(f"wflow {self._host} POST {TOKEN_PATH} could not be reached: {reason}.") from error
        if response.is_error:
            detail = _oauth_error(response)
            described = f" ({detail})" if detail else ""
            raise WflowApiError(
                f"wflow {self._host} POST {TOKEN_PATH} returned {response.status_code}{described}.",
                status=response.status_code,
                method="POST",
                path=TOKEN_PATH,
                detail=detail,
            )
        missing = f"wflow {self._host} POST {TOKEN_PATH} answered without an access_token."
        try:
            body = response.json()
            token = body["access_token"]
            expires_in = float(body.get("expires_in") or 0)
        except (ValueError, KeyError, TypeError) as error:
            raise WflowError(missing) from error
        if not isinstance(token, str) or not token:
            raise WflowError(missing)
        return token, time.monotonic() + max(expires_in - REFRESH_MARGIN_SECONDS, 0)
