from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx


class OllamaError(Exception):
    """Base exception for Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server cannot be reached."""


class OllamaTimeoutError(OllamaError):
    """Raised when an Ollama request times out."""


class OllamaHTTPError(OllamaError):
    """Raised when Ollama returns a non-2xx HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Ollama HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns invalid JSON or an unexpected payload structure."""


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for an installed Ollama model."""

    name: str
    model: str
    size: int | None = None
    digest: str | None = None
    modified_at: str | None = None
    details: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ModelInfo:
        if not isinstance(data, Mapping):
            raise OllamaResponseError("Model item must be a mapping")
        name = data.get("name") or data.get("model")
        if not name or not isinstance(name, str):
            raise OllamaResponseError("Model item missing required 'name' or 'model' field")
        model = data.get("model", name)
        size = data.get("size")
        digest = data.get("digest")
        modified_at = data.get("modified_at")
        details = data.get("details") if isinstance(data.get("details"), dict) else None
        return cls(
            name=name,
            model=model if isinstance(model, str) else name,
            size=size if isinstance(size, int) else None,
            digest=digest if isinstance(digest, str) else None,
            modified_at=modified_at if isinstance(modified_at, str) else None,
            details=details,
        )


class OllamaClient:
    """Asynchronous client for interacting with a local or remote Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        *,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._injected_client = client
        self._owns_client = client is None
        self._client: httpx.AsyncClient | None = client

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._injected_client is not None:
            if self._injected_client.is_closed:
                raise OllamaConnectionError("Injected HTTP client is already closed")
            return self._injected_client

        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def is_reachable(self) -> bool:
        """Check whether the Ollama server is reachable and responding."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except (httpx.RequestError, OllamaConnectionError):
            return False

    async def list_models(self) -> list[ModelInfo]:
        """Fetch installed models from GET /api/tags."""
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise OllamaHTTPError(response.status_code, response.text)
            try:
                data = response.json()
            except ValueError as err:
                raise OllamaResponseError(f"Malformed JSON response: {err}") from err

            if not isinstance(data, dict) or "models" not in data:
                raise OllamaResponseError("Expected JSON object with 'models' key")

            models_data = data["models"]
            if not isinstance(models_data, list):
                raise OllamaResponseError("'models' must be a list")

            return [ModelInfo.from_dict(item) for item in models_data]
        except httpx.TimeoutException as err:
            raise OllamaTimeoutError(f"Timed out connecting to Ollama at {self.base_url}: {err}") from err
        except httpx.RequestError as err:
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self.base_url}: {err}") from err

    async def chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        *,
        options: Mapping[str, Any] | None = None,
    ) -> str:
        """Send a non-streaming chat completion request to POST /api/chat.

        Returns:
            The assistant response text from message.content.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": False,
        }
        if options:
            payload["options"] = dict(options)

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            if response.status_code != 200:
                raise OllamaHTTPError(response.status_code, response.text)

            try:
                data = response.json()
            except ValueError as err:
                raise OllamaResponseError(f"Malformed JSON response: {err}") from err

            if not isinstance(data, dict):
                raise OllamaResponseError("Expected JSON object response")

            message_obj = data.get("message")
            if not isinstance(message_obj, dict):
                raise OllamaResponseError("Response missing 'message' object")

            content = message_obj.get("content")
            if not isinstance(content, str):
                raise OllamaResponseError("Message missing 'content' string")

            return content
        except httpx.TimeoutException as err:
            raise OllamaTimeoutError(f"Timed out waiting for chat response: {err}") from err
        except httpx.RequestError as err:
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self.base_url}: {err}") from err

    async def aclose(self) -> None:
        """Close the underlying client if managed by this instance."""
        if self._owns_client and self._client is not None:
            if not self._client.is_closed:
                await self._client.aclose()
            self._client = None
