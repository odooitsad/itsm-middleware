import httpx

from src.core.logger import get_logger

logger = get_logger(__name__)


class HttpxClient:
    """
    HTTP client wrapper around httpx.AsyncClient with built-in error handling and logging.
        - Designed for use in ITSM adapters but can be reused for other HTTP interactions.
        - Provides methods for GET and POST requests with optional headers and parameters.
        - Can be extended with additional HTTP methods (PUT, DELETE, etc.) as needed.
        - Supports both fixed base URL mode (for specific APIs) and generic mode (for multi-tenant scenarios).
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
    ) -> httpx.Response:
        return await self._request("GET", path, headers=headers, **kwargs)

    async def post(
        self, path: str, *, headers: dict | None = None, **kwargs
    ) -> httpx.Response:
        return await self._request("POST", path, headers=headers, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Internal method to handle HTTP requests with error handling."""
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP %s %s returned %s: %s",
                method,
                exc.request.url,
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.RequestError as exc:
            logger.error("HTTP %s %s failed: %s", method, exc.request.url, exc)
            raise

        logger.debug("HTTP %s %s → %s", method, path, response.status_code)
        return response
