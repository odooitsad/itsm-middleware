from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx

from src.core.logger import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class AuthType(StrEnum):
    NONE = "none"
    BEARER = "bearer"          # static token supplied at construction
    BASIC = "basic"            # username + password via HTTP Basic
    API_KEY_HEADER = "api_key_header"
    JWT_FROM_API = "jwt_from_api"  # token fetched from a POST login endpoint and auto-refreshed


@dataclass
class JwtProviderConfig:
    """
    Configuration for fetching and caching a JWT from the ITSM login endpoint.

    The client will POST to `login_path` with a JSON body built from
    `username_field`/`password_field`, parse `token_field` from the response,
    and cache it until `ttl_seconds - refresh_buffer_seconds` have elapsed.

    Example for BMC Helix:
        JwtProviderConfig(
            login_path="/api/jwt/login",
            username="svc-account",
            password="s3cr3t",
            token_field="token",
            ttl_seconds=3600,
        )
    """

    login_path: str
    username: str
    password: str
    username_field: str = "username"
    password_field: str = "password"
    token_field: str = "token"
    ttl_seconds: float = 3600.0
    refresh_buffer_seconds: float = 30.0


class _JwtTokenProvider:
    """Internal token lifecycle handler. Fetches, caches, and refreshes the JWT."""

    def __init__(self, client: httpx.AsyncClient, config: JwtProviderConfig) -> None:
        self._client = client
        self._config = config
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def get_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at:
            return self._token
        return await self._fetch()

    async def _fetch(self) -> str:
        config = self._config
        logger.debug("Fetching JWT token from %s", config.login_path)
        try:
            response = await self._client.post(
                config.login_path,
                json={config.username_field: config.username, config.password_field: config.password},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "JWT login failed: POST %s returned %s: %s",
                config.login_path,
                exc.response.status_code,
                exc.response.text,
            )
            raise

        token = response.json()[config.token_field]
        self._token = token
        self._expires_at = time.monotonic() + config.ttl_seconds - config.refresh_buffer_seconds
        logger.debug("JWT token acquired, valid for ~%.0fs", config.ttl_seconds - config.refresh_buffer_seconds)
        return token

    def invalidate(self) -> None:
        """Force a re-fetch on the next request (e.g. after a 401 response)."""
        self._token = None
        self._expires_at = 0.0


class HttpxClient:
    """
    Long-lived async HTTP client for outbound ITSM integrations.

    Designed to be created once at application startup, stored on `app.state`,
    and injected into adapters via FastAPI dependencies.

    Auth strategies (AuthType):
    - NONE           — no authentication
    - BEARER         — static Bearer token supplied at construction
    - BASIC          — HTTP Basic (username + password)
    - API_KEY_HEADER — custom header key/value
    - JWT_FROM_API   — token fetched from a POST login endpoint, cached and
                       auto-refreshed before expiry (requires `jwt_config`)

    Lifecycle:
        # In lifespan:
        client = HttpxClient(base_url=..., auth_type=AuthType.JWT_FROM_API, jwt_config=...)
        await client.start()
        app.state.bmc_helix_http = client
        yield
        await client.stop()

    Short-lived (tests / scripts):
        async with HttpxClient(...) as client:
            data = await client.get("/endpoint")
    """

    def __init__(
        self,
        base_url: str = "",
        *,
        auth_type: AuthType = AuthType.NONE,
        # --- static auth ---
        auth_value: str = "",
        auth_username: str = "",
        auth_password: str = "",
        api_key_header_name: str = "X-Api-Key",
        # --- JWT auth ---
        jwt_config: JwtProviderConfig | None = None,
        # --- general ---
        extra_headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        if auth_type is AuthType.JWT_FROM_API and jwt_config is None:
            raise ValueError("jwt_config is required when auth_type=JWT_FROM_API")

        self._base_url = base_url.rstrip("/")
        self._auth_type = auth_type
        self._auth_value = auth_value
        self._auth_username = auth_username
        self._auth_password = auth_password
        self._api_key_header_name = api_key_header_name
        self._jwt_config = jwt_config
        self._extra_headers = extra_headers or {}
        self._timeout = httpx.Timeout(timeout)
        self._client: httpx.AsyncClient | None = None
        self._jwt_provider: _JwtTokenProvider | None = None

    # ------------------------------------------------------------------
    # Lifecycle — long-lived (lifespan) usage
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Open the underlying httpx.AsyncClient. Call once at app startup."""
        self._client = self._build_client()
        if self._auth_type is AuthType.JWT_FROM_API:
            assert self._jwt_config is not None
            self._jwt_provider = _JwtTokenProvider(self._client, self._jwt_config)

    async def stop(self) -> None:
        """Close the underlying httpx.AsyncClient. Call once at app shutdown."""
        await self.aclose()

    # ------------------------------------------------------------------
    # Lifecycle — short-lived (context manager) usage
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "HttpxClient":
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._jwt_provider = None

    # ------------------------------------------------------------------
    # Internal client construction
    # ------------------------------------------------------------------

    def _build_client(self) -> httpx.AsyncClient:
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        headers.update(self._extra_headers)
        auth: httpx.Auth | None = None

        match self._auth_type:
            case AuthType.BEARER:
                headers["Authorization"] = f"Bearer {self._auth_value}"
            case AuthType.BASIC:
                auth = httpx.BasicAuth(self._auth_username, self._auth_password)
            case AuthType.API_KEY_HEADER:
                headers[self._api_key_header_name] = self._auth_value
            case AuthType.JWT_FROM_API | AuthType.NONE:
                pass  # JWT header is injected per-request; NONE has no auth

        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            auth=auth,
            timeout=self._timeout,
        )

    # ------------------------------------------------------------------
    # HTTP Methods
    # ------------------------------------------------------------------

    async def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("POST", path, body=body)

    async def put(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("PUT", path, body=body)

    async def patch(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("PATCH", path, body=body)

    async def delete(
        self,
        path: str,
    ) -> dict[str, Any]:
        return await self._request("DELETE", path)

    # ------------------------------------------------------------------
    # Internal request execution
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError(
                "HttpxClient is not started. Call await client.start() or use it as "
                "an async context manager (async with HttpxClient(...) as client:)."
            )

        logger.debug("HTTP %s %s%s params=%s", method, self._base_url, path, params)

        headers: dict[str, str] = {}
        if self._auth_type is AuthType.JWT_FROM_API:
            assert self._jwt_provider is not None
            token = await self._jwt_provider.get_token()
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self._client.request(
                method,
                path,
                params=params,
                json=body,
                headers=headers,
            )
            if response.status_code == 401 and self._auth_type is AuthType.JWT_FROM_API:
                # Token may have been invalidated server-side — force one refresh
                assert self._jwt_provider is not None
                self._jwt_provider.invalidate()
                token = await self._jwt_provider.get_token()
                headers["Authorization"] = f"Bearer {token}"
                response = await self._client.request(
                    method, path, params=params, json=body, headers=headers
                )
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

        if response.content:
            return response.json()
        return {}
