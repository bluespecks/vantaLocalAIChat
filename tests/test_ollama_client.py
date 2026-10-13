import httpx
import pytest

from vanta.ollama_client import (
    ModelInfo,
    OllamaClient,
    OllamaConnectionError,
    OllamaHTTPError,
    OllamaResponseError,
    OllamaTimeoutError,
)


@pytest.mark.asyncio
async def test_is_reachable_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)
        assert await client.is_reachable() is True


@pytest.mark.asyncio
async def test_is_reachable_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)
        assert await client.is_reachable() is False


@pytest.mark.asyncio
async def test_list_models_success():
    payload = {
        "models": [
            {
                "name": "gemma3:4b",
                "model": "gemma3:4b",
                "size": 3338801804,
                "digest": "a2af6cc3eb7f",
                "modified_at": "2026-10-07T11:54:01Z",
                "details": {
                    "family": "gemma3",
                    "parameter_size": "4.3B",
                    "quantization_level": "Q4_K_M",
                },
            },
            {
                "name": "gemma4:12b",
                "model": "gemma4:12b",
                "size": 7556508396,
                "digest": "4eb23ef187e2",
                "modified_at": "2026-09-09T22:26:27Z",
                "details": {
                    "family": "gemma4",
                    "parameter_size": "11.9B",
                },
            },
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)
        models = await client.list_models()

        assert len(models) == 2
        assert isinstance(models[0], ModelInfo)
        assert models[0].name == "gemma3:4b"
        assert models[0].size == 3338801804
        assert models[0].details == {
            "family": "gemma3",
            "parameter_size": "4.3B",
            "quantization_level": "Q4_K_M",
        }
        assert models[1].name == "gemma4:12b"


@pytest.mark.asyncio
async def test_chat_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        assert request.method == "POST"
        return httpx.Response(
            200,
            json={
                "model": "gemma3:4b",
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am ready to help.",
                },
                "done": True,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)
        response_text = await client.chat(
            model="gemma3:4b",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert response_text == "Hello! I am ready to help."


@pytest.mark.asyncio
async def test_connection_error_handling():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)

        with pytest.raises(OllamaConnectionError) as exc_info:
            await client.list_models()
        assert "Failed to connect" in str(exc_info.value)

        with pytest.raises(OllamaConnectionError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert "Failed to connect" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_error_handling():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Read timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)

        with pytest.raises(OllamaTimeoutError):
            await client.list_models()

        with pytest.raises(OllamaTimeoutError):
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_http_error_handling():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)

        with pytest.raises(OllamaHTTPError) as exc_info:
            await client.list_models()
        assert exc_info.value.status_code == 500

        with pytest.raises(OllamaHTTPError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_malformed_json_handling():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not valid json")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)

        with pytest.raises(OllamaResponseError) as exc_info:
            await client.list_models()
        assert "Malformed JSON" in str(exc_info.value)

        with pytest.raises(OllamaResponseError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert "Malformed JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unexpected_payload_shape_handling():
    def handler_list(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected_key": 123})

    transport_list = httpx.MockTransport(handler_list)
    async with httpx.AsyncClient(transport=transport_list) as mock_client:
        client = OllamaClient(client=mock_client)
        with pytest.raises(OllamaResponseError) as exc_info:
            await client.list_models()
        assert "Expected JSON object with 'models' key" in str(exc_info.value)

    def handler_chat_missing_msg(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"done": True})

    transport_chat = httpx.MockTransport(handler_chat_missing_msg)
    async with httpx.AsyncClient(transport=transport_chat) as mock_client:
        client = OllamaClient(client=mock_client)
        with pytest.raises(OllamaResponseError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert "Response missing 'message' object" in str(exc_info.value)

    def handler_chat_missing_content(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"role": "assistant"}})

    transport_chat2 = httpx.MockTransport(handler_chat_missing_content)
    async with httpx.AsyncClient(transport=transport_chat2) as mock_client:
        client = OllamaClient(client=mock_client)
        with pytest.raises(OllamaResponseError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert "Message missing 'content' string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_base_url_normalization():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://localhost:11434/api/tags"
        return httpx.Response(200, json={"models": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(base_url="http://localhost:11434///", client=mock_client)
        assert client.base_url == "http://localhost:11434"
        assert await client.is_reachable() is True


@pytest.mark.asyncio
async def test_is_reachable_http_errors_and_protocol_errors():
    def handler_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_500)) as mock_client:
        client = OllamaClient(client=mock_client)
        assert await client.is_reachable() is False

    def handler_503(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_503)) as mock_client:
        client = OllamaClient(client=mock_client)
        assert await client.is_reachable() is False

    def handler_protocol(request: httpx.Request) -> httpx.Response:
        raise httpx.RemoteProtocolError("Server disconnected unexpectedly")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_protocol)) as mock_client:
        client = OllamaClient(client=mock_client)
        assert await client.is_reachable() is False


@pytest.mark.asyncio
async def test_chat_options_passed():
    captured_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        import json
        captured_payload = json.loads(request.content)
        return httpx.Response(
            200,
            json={"model": "gemma3:4b", "message": {"role": "assistant", "content": "ok"}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)
        await client.chat(
            model="gemma3:4b",
            messages=[{"role": "user", "content": "hi"}],
            options={"temperature": 0.2, "num_predict": 128},
        )
        assert captured_payload.get("options") == {"temperature": 0.2, "num_predict": 128}
        assert captured_payload.get("model") == "gemma3:4b"
        assert captured_payload.get("stream") is False


@pytest.mark.asyncio
async def test_internal_client_reuse_and_aclose():
    client = OllamaClient()
    c1 = await client._get_client()
    c2 = await client._get_client()
    assert c1 is c2
    assert not c1.is_closed

    # aclose should close internally created client
    await client.aclose()
    assert c1.is_closed
    assert client._client is None

    # idempotent aclose
    await client.aclose()


@pytest.mark.asyncio
async def test_aclose_does_not_close_injected_client():
    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    client = OllamaClient(client=mock_client)
    await client.aclose()
    assert not mock_client.is_closed
    await mock_client.aclose()


@pytest.mark.asyncio
async def test_async_context_manager_cleanup():
    # Internally owned client is closed on context exit
    async with OllamaClient() as client:
        internal_client = await client._get_client()
        assert not internal_client.is_closed
    assert internal_client.is_closed

    # Injected client is not closed on context exit
    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    async with OllamaClient(client=mock_client) as client:
        pass
    assert not mock_client.is_closed
    await mock_client.aclose()


@pytest.mark.asyncio
async def test_injected_client_already_closed():
    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    await mock_client.aclose()
    client = OllamaClient(client=mock_client)

    assert await client.is_reachable() is False

    with pytest.raises(OllamaConnectionError) as exc_info_list:
        await client.list_models()
    assert "Injected HTTP client is already closed" in str(exc_info_list.value)

    with pytest.raises(OllamaConnectionError) as exc_info_chat:
        await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
    assert "Injected HTTP client is already closed" in str(exc_info_chat.value)


@pytest.mark.asyncio
async def test_protocol_errors_translation():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.RemoteProtocolError("Premature connection termination")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        client = OllamaClient(client=mock_client)

        with pytest.raises(OllamaConnectionError) as exc_info:
            await client.list_models()
        assert "Failed to connect" in str(exc_info.value)

        with pytest.raises(OllamaConnectionError) as exc_info:
            await client.chat(model="gemma3:4b", messages=[{"role": "user", "content": "hi"}])
        assert "Failed to connect" in str(exc_info.value)

