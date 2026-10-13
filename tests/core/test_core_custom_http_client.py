import pytest

from app.core.custom_http_client import CustomAsyncClient


@pytest.mark.asyncio
async def test_custom_async_client_default_concurrency():
    """Test CustomAsyncClient defaults to max_concurrency of 20."""
    client = CustomAsyncClient()
    assert hasattr(client, "semaphore")
    assert client.semaphore._value == 20
    await client.aclose()


@pytest.mark.asyncio
async def test_custom_async_client_custom_concurrency():
    """Test CustomAsyncClient respects custom max_concurrency parameter."""
    client = CustomAsyncClient(max_concurrency=7)
    assert hasattr(client, "semaphore")
    assert client.semaphore._value == 7
    await client.aclose()
