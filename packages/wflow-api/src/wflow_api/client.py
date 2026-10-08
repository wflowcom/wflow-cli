"""Calls to the wflow public API, signed with the caller's token."""

from collections.abc import Awaitable, Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

from wflow_api.errors import WflowApiError, WflowError
from wflow_api.guards import filename_from_disposition, problem_detail
from wflow_api.models.common import FileContent

Token = Callable[[], Awaitable[str]]

UPLOAD_TIMEOUT = 120
DOWNLOAD_TIMEOUT = 60


class WflowClient:
    def __init__(
        self,
        token: Token,
        *,
        api_base: str,
        headers: Mapping[str, str],
        timeout: float = 30,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_base = api_base
        self._token = token
        self._headers = dict(headers)
        self._timeout = timeout
        self._transport = transport
        self._host = urlsplit(api_base).netloc or api_base

    def _http(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.api_base, timeout=timeout, transport=self._transport)

    async def _signed(self) -> dict[str, str]:
        return {**self._headers, "Authorization": f"Bearer {await self._token()}"}

    def _failure(self, response: httpx.Response, method: str, path: str) -> WflowApiError:
        detail = problem_detail(response)
        return WflowApiError(
            f"wflow {self._host} {method} {path} returned {response.status_code}.{detail}",
            status=response.status_code,
            method=method,
            path=path,
            detail=detail.strip(),
        )

    def _transport_failure(self, error: httpx.HTTPError | httpx.InvalidURL, method: str, path: str) -> WflowError:
        return WflowError(
            f"wflow {self._host} {method} {path} failed: {type(error).__name__}{f': {error}' if str(error) else ''}."
        )

    async def request(self, method: str, path: str, *, timeout: float | None = None, **kwargs: Any) -> Any:
        headers = {**await self._signed(), "Accept": "application/json"}
        try:
            async with self._http(self._timeout if timeout is None else timeout) as http:
                response = await http.request(method, path, headers=headers, **kwargs)
        except (httpx.HTTPError, httpx.InvalidURL) as error:
            raise self._transport_failure(error, method, path) from error
        if not response.is_success:
            raise self._failure(response, method, path)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as error:
            raise WflowError(
                f"wflow {self._host} {method} {path} returned a {response.status_code} that was not JSON."
            ) from error

    async def upload(
        self,
        method: str,
        path: str,
        filename: str,
        content: bytes,
        params: dict[str, object] | None = None,
        field: str = "file",
    ) -> Any:
        return await self.request(
            method, path, params=params or {}, files={field: (filename, content)}, timeout=UPLOAD_TIMEOUT
        )

    async def download(
        self, path: str, method: str = "GET", json: Any = None, max_bytes: int | None = None
    ) -> FileContent:
        headers = await self._signed()
        try:
            async with (
                self._http(DOWNLOAD_TIMEOUT) as http,
                http.stream(method, path, headers=headers, json=json) as response,
            ):
                if response.is_error:
                    await response.aread()
                    raise self._failure(response, method, path)
                if response.status_code != 200:
                    await response.aread()
                    if response.status_code == 204:
                        raise WflowError(
                            f"wflow {self._host} {method} {path} returned 204: wflow holds no content for that file."
                        )
                    raise WflowError(f"wflow {self._host} {method} {path} returned {response.status_code}, not 200.")
                try:
                    declared = int(response.headers.get("content-length") or 0)
                except ValueError:
                    raise WflowError(f"wflow {self._host} {method} {path} sent a non-numeric Content-Length.") from None
                if max_bytes is not None and declared > max_bytes:
                    raise WflowError(
                        f"The file at {path} is {declared} bytes, over the {max_bytes}-byte limit set for this download."
                    )
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if max_bytes is not None and size > max_bytes:
                        raise WflowError(
                            f"The file at {path} is over the {max_bytes}-byte limit set for this download."
                        )
                    chunks.append(chunk)
                return FileContent(
                    filename=filename_from_disposition(response.headers.get("content-disposition", "")),
                    content_type=response.headers.get("content-type"),
                    content=b"".join(chunks),
                )
        except (httpx.HTTPError, httpx.InvalidURL) as error:
            raise self._transport_failure(error, method, path) from error
