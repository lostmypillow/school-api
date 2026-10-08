import hashlib
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from app.domains.tasks.scrape_to_parquet import (
    _append_to_parquet,
    _read_parquet_records,
    _safe_int,
    scrape_to_parquet,
    fetch_html,
    scrape,
)
from tests.conftest import MockHTTPClient, MockRedis


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------


def test_safe_int():
    """Test _safe_int helper correctly parses numbers and returns None on invalid inputs."""
    assert _safe_int(10) == 10
    assert _safe_int("10") == 10
    assert _safe_int(" 10 ") == 10
    assert _safe_int("10.0") == 10
    assert _safe_int(None) is None
    assert _safe_int("") is None
    assert _safe_int("N/A") is None


def test_append_and_read_parquet(temp_parquet_dir: Path):
    """Test _append_to_parquet creates parquet files and _read_parquet_records reads them."""
    data = [{"id": "112_1", "year": "112", "sem": "1", "link": "link"}]
    file_path = _append_to_parquet("semesters", data, temp_parquet_dir)
    assert file_path.exists()

    records = _read_parquet_records(file_path)
    assert len(records) == 1
    assert records[0]["id"] == "112_1"


# ---------------------------------------------------------------------------
# Tests for fetch_html
# ---------------------------------------------------------------------------


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
    mock_req = httpx.Request("GET", url)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=mock_req, response=mock_resp
    )
    client.get_mock.return_value = mock_resp

    ctx = {"redis": mock_redis, "client": client}

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_html(ctx, mock_redis, url)


# ---------------------------------------------------------------------------
# Tests for scrape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_sem_tag(mock_redis: MockRedis):
    """Test scrape with tag='sem' finds only <a> tags where href starts with 'Subj'."""
    url_path = "sem_index.jsp"
    full_url = "https://aps.ntut.edu.tw/course/tw/" + url_path
    html_content = """
    <html>
        <body>
            <a href="Subj.jsp?format=-2&year=112&sem=1">112-1</a>
            <a href="Subj.jsp?format=-2&year=112&sem=2">112-2</a>
            <a href="Other.jsp?action=test">Other Link</a>
            <span>Not a link</span>
        </body>
    </html>
    """
    client = MockHTTPClient(responses={full_url: html_content})
    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="sem")
    assert len(results) == 2
    assert [r.text for r in results] == ["112-1", "112-2"]
    assert all(r["href"].startswith("Subj") for r in results)


@pytest.mark.asyncio
async def test_scrape_a_tag(mock_redis: MockRedis):
    """Test scrape with tag='a' extracts all <a> tags using lxml."""
    url_path = "dept_list.jsp"
    full_url = "https://aps.ntut.edu.tw/course/tw/" + url_path
    html_content = """
    <html>
        <body>
            <a href="Subj.jsp?year=112&sem=1&code=300">CS Dept</a>
            <a href="Subj.jsp?year=112&sem=1&code=301">EE Dept</a>
        </body>
    </html>
    """
    client = MockHTTPClient(responses={full_url: html_content})
    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="a")
    assert len(results) == 2
    assert results[0].text == "CS Dept"
    assert results[1].text == "EE Dept"


@pytest.mark.asyncio
async def test_scrape_tr_tag(mock_redis: MockRedis):
    """Test scrape with tag='tr' extracts all <tr> elements."""
    url_path = "course_list.jsp"
    full_url = "https://aps.ntut.edu.tw/course/tw/" + url_path
    html_content = """
    <table>
        <tr><th>Header</th></tr>
        <tr><td>Row 1</td></tr>
        <tr><td>Row 2</td></tr>
    </table>
    """
    client = MockHTTPClient(responses={full_url: html_content})
    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="tr")
    assert len(results) == 3


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
        "502 Bad Gateway", request=mock_req, response=mock_resp
    )
    client.get_mock.return_value = mock_resp

    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="a")
    assert len(results) == 1
    assert results[0].name == "error"


# ---------------------------------------------------------------------------
# Tests for bootstrap_sqlite (scrape directly to parquet)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bootstrap_sqlite_semester_generation(
    temp_parquet_dir: Path, mock_redis: MockRedis
):
    """Test bootstrap_sqlite generates semesters starting from current ROC year down to 86."""
    client = MockHTTPClient()
    ctx = {"parquet_dir": temp_parquet_dir, "redis": mock_redis, "client": client}

    await scrape_to_parquet(ctx)

    sem_records = _read_parquet_records(temp_parquet_dir / "semesters.parquet")
    assert len(sem_records) > 0

    current_roc_year = date.today().year - 1911
    years = [int(s["year"]) for s in sem_records]
    assert max(years) == current_roc_year
    assert min(years) == 85


@pytest.mark.asyncio
async def test_bootstrap_sqlite_full_pipeline(
    temp_parquet_dir: Path, mock_redis: MockRedis
):
    """Test complete bootstrap_sqlite pipeline from semesters -> departments -> dept years -> courses."""
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=300"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=3010"

    dept_html = f"""
    <html>
        <body>
            <a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=300">Department of Computer Science</a>
        </body>
    </html>
    """

    dy_html = f"""
    <html>
        <body>
            <a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=3010">CS Year 1</a>
        </body>
    </html>
    """

    course_html = """
    <table>
        <tr>
            <td>300001</td>
            <td>Introduction to Programming</td>
            <td>3</td>
            <td>3</td>
            <td>3</td>
            <td>Required</td>
            <td>Prof. Alan Turing</td>
            <td></td>
            <td>1 2 3</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td>Room 101</td>
            <td>50</td>
            <td>1</td>
            <td>Chinese</td>
            <td><a href="syllabus.jsp?id=300001">Syllabus</a></td>
            <td>Prerequisites apply</td>
            <td>None</td>
            <td>No</td>
            <td>No</td>
        </tr>
    </table>
    """

    responses = {
        sem_url: dept_html,
        dept_url: dy_html,
        dy_url: course_html,
    }

    client = MockHTTPClient(responses=responses)
    ctx = {"parquet_dir": temp_parquet_dir, "redis": mock_redis, "client": client}

    await scrape_to_parquet(ctx)

    # 1. Verify departments saved
    dept_records = _read_parquet_records(temp_parquet_dir / "departments.parquet")
    assert len(dept_records) >= 1

    # 2. Verify department years saved
    dy_records = _read_parquet_records(temp_parquet_dir / "department_years.parquet")
    assert len(dy_records) >= 1

    # 3. Verify courses saved
    courses = _read_parquet_records(temp_parquet_dir / "courses.parquet")
    assert len(courses) >= 1
    assert courses[0]["name"] == "Introduction to Programming"
    assert courses[0]["credits"] == 3
