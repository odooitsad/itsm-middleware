from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

import httpx

from src.core.exceptions import HttpClientError
from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HttpResponse:
    """
    Generic, framework-agnostic representation of an HTTP response.

    Consumers of HttpClient depend only on this dataclass, never on httpx types,
    so the underlying HTTP library can be swapped without touching callers.
    """

    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    json: Any = None

    @classmethod
    def from_httpx(cls, response: httpx.Response) -> "HttpResponse":
        try:
            body = response.json()
        except JSONDecodeError:
            logger.warning(
                "Response body is not valid JSON. Returning raw text instead."
            )
            body = None
        return cls(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            text=response.text,
            json=body,
        )


class HttpClient:
    """
    HTTP client wrapper around httpx.AsyncClient with built-in error handling and logging.
        - Designed for use in ITSM adapters but can be reused for other HTTP interactions.
        - Provides methods for GET and POST requests with optional headers and parameters.
        - Can be extended with additional HTTP methods (PUT, DELETE, etc.) as needed.
        - Supports both fixed base URL mode (for specific APIs) and generic mode (for multi-tenant scenarios).
        - Returns/raises only HttpResponse and HttpClientError, keeping httpx fully
          encapsulated so callers never depend on it directly.
    """

    def __init__(
        self,
        base_url: str = "",
        auth: httpx.Auth | None = None,
        headers: dict | None = None,
        timeout: float = 10.0,
        **kwargs,
    ):
        self._client = httpx.AsyncClient(
            base_url=base_url, auth=auth, headers=headers, timeout=timeout, **kwargs
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get(
        self, path: str, *, headers: dict | None = None, **kwargs
    ) -> HttpResponse:
        return await self._request("GET", path, headers=headers, **kwargs)

    async def post(
        self, path: str, *, headers: dict | None = None, **kwargs
    ) -> HttpResponse:
        return await self._request("POST", path, headers=headers, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> HttpResponse:
        """Internal method to handle HTTP requests with error handling."""

        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            http_response = HttpResponse.from_httpx(exc.response)
            json_text = (
                http_response.json
                if http_response.json is not None
                else http_response.text
            )
            logger.error(
                "HTTP %s %s returned %s: %s",
                method,
                exc.request.url,
                http_response.status_code,
                json_text,
            )
            raise HttpClientError(str(exc), response=http_response) from exc
        except httpx.RequestError as exc:
            logger.error("HTTP %s %s failed: %s", method, exc.request.url, exc)
            raise HttpClientError(str(exc)) from exc

        logger.debug("HTTP %s %s → %s", method, path, response.status_code)
        return HttpResponse.from_httpx(response)
