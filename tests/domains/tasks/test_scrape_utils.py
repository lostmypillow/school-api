import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from app.domains.tasks.parquet_utils import (
    _safe_int,
    append_to_parquet,
    read_parquet_records,
)
from app.domains.tasks.scrape_utils import fetch_html, scrape
from tests.conftest import MockHTTPClient, MockRedis


def test_safe_int():
    """Test _safe_int helper correctly parses numbers and returns None on invalid inputs."""
    assert _safe_int(10) == 10
    assert _safe_int("10") == 10
    assert _safe_int(" 10 ") == 10
    assert _safe_int("10.0") == 10
    assert _safe_int(None) is None
    assert _safe_int("") is None
    assert _safe_int("N/A") is None


async def test_append_and_read_parquet(temp_parquet_dir: Path):
    """Test _append_to_parquet creates parquet files and _read_parquet_records reads them."""
    data = [{"id": "112_1", "year": "112", "sem": "1", "link": "link"}]
    file_path = await append_to_parquet("semesters", data, temp_parquet_dir)
    assert file_path.exists()

    records = read_parquet_records(file_path)
    assert len(records) == 1
    assert records[0]["id"] == "112_1"


@pytest.mark.asyncio
async def test_fetch_html_cache_hit_string(mock_redis: MockRedis):
    """Test fetch_html returns cached string directly without calling HTTP client."""
    url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year=112&sem=1"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_key = f"cache:html:{url_hash}"

    expected_html = "<html><body>Cached String Content</body></html>"
    await mock_redis.set(cache_key, expected_html)

    client = MockHTTPClient()
    ctx = {"redis": mock_redis, "client": client}

    result = await fetch_html(ctx, mock_redis, url)
    assert result == expected_html
    client.get_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_html_cache_hit_bytes(mock_redis: MockRedis):
    """Test fetch_html decodes cached bytes to utf-8 string."""
    url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year=112&sem=2"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_key = f"cache:html:{url_hash}"

    expected_html = "<html><body>Cached Bytes 測試</body></html>"
    await mock_redis.set(cache_key, expected_html.encode("utf-8"))

    client = MockHTTPClient()
    ctx = {"redis": mock_redis, "client": client}

    result = await fetch_html(ctx, mock_redis, url)
    assert result == expected_html
    client.get_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_html_cache_miss(mock_redis: MockRedis):
    """Test fetch_html fetches from HTTP client on cache miss and stores in Redis."""
    url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year=111&sem=1"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_key = f"cache:html:{url_hash}"

    raw_html = "<html><body>Fetched Fresh HTML</body></html>"
    client = MockHTTPClient(responses={url: raw_html})
    ctx = {"redis": mock_redis, "client": client}

    result = await fetch_html(ctx, mock_redis, url, ttl_seconds=3600)
    assert result == raw_html

    cached = await mock_redis.get(cache_key)
    assert cached == raw_html


@pytest.mark.asyncio
async def test_fetch_html_http_status_error(mock_redis: MockRedis):
    """Test fetch_html propagates HTTP errors when client returns non-200."""
    url = "https://aps.ntut.edu.tw/course/tw/error_page.jsp"

    client = MockHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    mock_req = httpx.Request(method="GET", url=url)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="404 Not Found", request=mock_req, response=mock_resp
    )
    client.get_mock.return_value = mock_resp

    ctx = {"redis": mock_redis, "client": client}

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_html(ctx, mock_redis, url)


@pytest.mark.asyncio
async def test_scrape_http_error_handling(mock_redis: MockRedis):
    """Test scrape catches httpx.HTTPError and returns <error></error> elements."""
    url_path = "failing_endpoint.jsp"
    full_url = "https://aps.ntut.edu.tw/course/tw/" + url_path

    client = MockHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 502
    mock_resp.text = "Bad Gateway"
    mock_req = httpx.Request("GET", full_url)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="502 Bad Gateway", request=mock_req, response=mock_resp
    )
    client.get_mock.return_value = mock_resp

    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="a")
    assert len(results) == 1
    assert results[0].name == "error"
