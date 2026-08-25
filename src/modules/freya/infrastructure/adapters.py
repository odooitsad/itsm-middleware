from src.core.clients.http import HttpClient
from src.core.exceptions import HttpClientError
from src.core.logger import get_logger
from src.modules.freya.domain.entities import AuthToken, FreyaResponse
from src.modules.freya.domain.exceptions import FreyaClientError
from src.modules.freya.domain.ports import (
    FreyaPort,
    NotificationPort,
    TroubleshootingPort,
)

logger = get_logger(__name__)


class FreyaAdapter(FreyaPort):
    """
    HTTP adapter for the Freya API.

    Handles authentication (login) and generic POST requests. Payload building
    and response interpretation for specific Freya operations (IM open/update/
    close) live in the application layer, which is the only consumer of
    `send_post_request`.
    """

    def __init__(self, client: HttpClient, username: str, password: str) -> None:
        self._client = client
        self._username = username
        self._password = password

    @classmethod
    def build(
        cls, base_url: str, username: str, password: str, timeout: float
    ) -> "FreyaAdapter":
        client = HttpClient(base_url=base_url, timeout=timeout)
        return cls(client, username, password)

    async def stop(self) -> None:
        await self._client.close()

    async def fetch_auth_token(self) -> str:
        """
        Fetch the authentication token from the Freya API.

        Errors handled by the Freya API:
        - 400: Bad Request
        - 401: Unauthorized

        Expected response body is a JSON object with the keys:
        - code: "0" (ok)   | "-1" (error),
        - desc: "OK"       | "Error",
        - results: "Token" | "Error Message"
        """
        payload = {"username": self._username, "password": self._password}
        try:
            response = await self._client.post("/Login", json=payload)
        except HttpClientError as exc:
            response = exc.response
            if response is None or response.json is None:
                raise
            json_res = response.json
            result = json_res.get("results")
            raise FreyaClientError(result, 401) from exc

        freya_response = FreyaResponse(**response.json)

        result = freya_response.get_result_text() or "Unknown error"
        if freya_response.has_an_error_code():
            logger.error("Auth - status %s - %s", response.status_code, result)
            raise FreyaClientError(result, 401)

        token = AuthToken(result)
        return token.authorization_header

    async def send_post_request(self, endpoint: str, payload: dict) -> str:
        """
        Send a POST request to the given Freya endpoint with the provided payload.

        If a required field is missing from the payload, the Freya API still
        responds with a 200 OK status, so the 'code' key in the response body
        must always be validated.

        Errors handled by the Freya API:
        - 400: Bad Request

        Expected response body is a JSON object with the keys:
        - code: "0" (ok)   | "-1" (error),
        - desc: "Ok"       | "Error",
        - results: "result" | "Error Message"
        """
        token = await self.fetch_auth_token()
        headers = {"Authorization": token}
        err_msg = f"Request ({endpoint})"

        try:
            response = await self._client.post(
                f"/{endpoint}", json=payload, headers=headers
            )
        except HttpClientError as exc:
            response = exc.response
            if response is None or response.json is None:
                raise
            json_res = response.json
            results = json_res.get("results") or json_res.get("detail", "Unknown error")
            raise FreyaClientError(results, response.status_code) from exc

        freya_response = FreyaResponse(**response.json)

        if freya_response.has_an_error_code():
            result = freya_response.get_result_text() or "Unknown error"
            status_code = 409 if "ya Creado" in result else response.status_code
            logger.error("%s - %s", err_msg, result)
            raise FreyaClientError(result, status_code)

        result = freya_response.results
        if isinstance(result, (list, dict)):
            logger.warning(
                "%s - Unexpected 'results' format: %s", err_msg, freya_response
            )
            raise FreyaClientError(f"Unexpected 'results' format: {result}")

        return result


class Notification(NotificationPort):
    """
    Best-effort adapter for sending fire-and-forget notifications.

    Delivery failures are logged and swallowed so a notification outage never
    interrupts the IM creation flow; the response body is not inspected.
    """

    def __init__(self, client: HttpClient) -> None:
        self._client = client

    @classmethod
    def build(cls, base_url: str, timeout: float) -> "Notification":
        client = HttpClient(base_url=base_url, timeout=timeout)
        return cls(client)

    async def stop(self) -> None:
        await self._client.close()

    async def notify_via_telegram(self, template: dict) -> None:
        logger.info("Sending notification via Telegram: %s", template)
        try:
            await self._client.post("/send/telegram/", json=template)
        except HttpClientError:
            logger.warning("Notification delivery failed")


class NullNotification(NotificationPort):
    """No-op notifier used when a client has notifications disabled."""

    async def stop(self) -> None:
        pass

    async def notify_via_telegram(self, template: dict) -> None:
        pass


class Troubleshooting(TroubleshootingPort):
    def __init__(self, client: HttpClient):
        self._client = client

    @classmethod
    def build(cls, base_url: str, timeout: float, token: str) -> "Troubleshooting":
        headers = {"X-Access-Token": token}
        client = HttpClient(
            base_url=base_url, timeout=timeout, headers=headers, verify=False
        )
        return cls(client)

    async def stop(self) -> None:
        await self._client.close()

    async def execute(self, im_id: str, ip_wan: str):
        payload = {"im": im_id, "ip_wan": ip_wan}
        logger.info(f"Triggering T-shoot for {ip_wan} - IM: {im_id}")
        try:
            response = await self._client.post("/parallel-th/exec", json=payload)
            task_id = response.json.get("task_id")
            logger.info(f"T-shoot executed successfully {task_id}")
        except HttpClientError:
            logger.warning("T-shoot execution failed")

    async def ping_last_mile(self, im_id: str, service_code: str):
        payload = {"im": im_id, "hostname": service_code}
        logger.info(f"Running last mile PING for Service: {service_code} - IM: {im_id}")
        try:
            response = await self._client.post(
                "/parallel-th/exec/ping-um", json=payload
            )
            logger.info("PING UM executed successfully: %s", response)
        except HttpClientError:
            logger.warning("PING UM execution failed")


class NullTroubleshooting(TroubleshootingPort):
    """No-op troubleshooting adapter used when a client has T-shooting disabled."""

    async def stop(self) -> None:
        pass

    async def execute(self, im_id: str, ip_wan: str):
        pass

    async def ping_last_mile(self, im_id: str, service_code: str):
        pass
