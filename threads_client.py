from typing import Any

import requests

THREADS_GRAPH_URL = "https://graph.threads.com"


class ThreadsAPIError(RuntimeError):
    pass


class ThreadsClient:
    """Small client for publishing text posts with Meta's Threads API."""

    def __init__(
        self,
        access_token: str,
        session: Any = requests,
        base_url: str = THREADS_GRAPH_URL,
    ) -> None:
        if not access_token:
            raise ValueError("A Threads access token is required.")
        self.access_token = access_token
        self.session = session
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/{path.lstrip('/')}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            data=data,
            timeout=60,
        )
        if not response.ok:
            try:
                payload = response.json()
                message = payload.get("error", {}).get("message")
            except (ValueError, AttributeError):
                message = None
            detail = message or f"HTTP {response.status_code}"
            raise ThreadsAPIError(f"Threads API request failed: {detail}")

        payload = response.json()
        if not payload.get("id"):
            raise ThreadsAPIError("Threads API response did not contain an id.")
        return payload

    def create_text_container(self, text: str) -> str:
        if not text.strip():
            raise ValueError("Threads post text cannot be empty.")
        payload = self._post(
            "me/threads",
            {"media_type": "TEXT", "text": text},
        )
        return str(payload["id"])

    def publish_container(self, creation_id: str) -> str:
        if not creation_id:
            raise ValueError("A creation id is required.")
        payload = self._post(
            "me/threads_publish",
            {"creation_id": creation_id},
        )
        return str(payload["id"])

    def publish_text(self, text: str) -> str:
        creation_id = self.create_text_container(text)
        return self.publish_container(creation_id)
