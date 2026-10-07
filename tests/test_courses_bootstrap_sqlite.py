import hashlib
from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.initialize import DB
from app.core.models import Course, Department, DepartmentYear, Semester
from app.domains.courses.bootstrap_sqlite import (
    bootstrap_sqlite,
    fetch_html,
    scrape,
)
from tests.conftest import MockHTTPClient, MockRedis


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

    # Verify cached in Redis
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


@pytest.mark.asyncio
async def test_scrape_general_exception_handling(mock_redis: MockRedis):
    """Test scrape catches generic Exception and returns <error></error> elements."""
    url_path = "broken.jsp"
    client = MockHTTPClient()
    client.get_mock.side_effect = RuntimeError("Unexpected connection crash")

    ctx = {"redis": mock_redis, "client": client}

    results = await scrape(ctx, url_path, tag="a")
    assert len(results) == 1
    assert results[0].name == "error"


# ---------------------------------------------------------------------------
# Tests for bootstrap_sqlite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bootstrap_sqlite_semester_generation(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Test bootstrap_sqlite generates semesters starting from current ROC year down to 86."""
    client = MockHTTPClient()
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    # Run bootstrap_sqlite
    await bootstrap_sqlite(ctx)

    # Check generated semesters in DB
    semesters = (
        await test_session.scalars(select(Semester).order_by(Semester.year.desc()))
    ).all()
    assert len(semesters) > 0

    current_roc_year = date.today().year - 1911
    years = [int(s.year) for s in semesters]
    assert max(years) == current_roc_year
    assert min(years) == 85  # Loop terminates when current_year goes from 86 to 85 (sem 2)

    # Verify link structure
    for s in semesters:
        assert s.link == f"Subj.jsp?format=-2&year={s.year}&sem={s.sem}"
        assert s.id == f"{s.year}_{s.sem}"


@pytest.mark.asyncio
async def test_bootstrap_sqlite_full_pipeline(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
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

    # Build 23-column valid course row
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
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    # Run bootstrap
    await bootstrap_sqlite(ctx)

    # 1. Verify departments saved
    dept_records = (await test_session.scalars(select(Department))).all()
    assert len(dept_records) >= 1
    target_dept = next(
        (d for d in dept_records if d.code == "300" and d.year == str(current_roc_year)),
        None,
    )
    assert target_dept is not None
    assert target_dept.name == "Department of Computer Science"
    assert target_dept.id == f"{current_roc_year}_{current_sem}_300"

    # 2. Verify department years saved
    dy_records = (await test_session.scalars(select(DepartmentYear))).all()
    assert len(dy_records) >= 1
    target_dy = next(
        (dy for dy in dy_records if dy.code == "3010" and dy.year == str(current_roc_year)),
        None,
    )
    assert target_dy is not None
    assert target_dy.name == "CS Year 1"
    assert target_dy.id == f"{current_roc_year}_{current_sem}_300_3010"

    # 3. Verify courses saved
    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) >= 1
    course = courses[0]
    assert course.code == "300001"
    assert course.name == "Introduction to Programming"
    assert course.credits == 3
    assert course.instructor == "Prof. Alan Turing"
    assert course.mon == "1 2 3"
    assert course.classroom == "Room 101"
    assert course.students_enrolled == 50
    assert course.students_dropped == 1
    assert course.language == "Chinese"
    assert course.link == "syllabus.jsp?id=300001"
    assert course.notes == "Prerequisites apply"


@pytest.mark.asyncio
async def test_bootstrap_sqlite_course_without_code_fallback_to_name(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Test course row with empty code column falls back to course name for ID generation."""
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=400"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=4010"

    dept_html = f'<a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=400">Design</a>'
    dy_html = f'<a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=4010">Design Year 1</a>'

    # Course row with empty code (cell 0)
    course_html = """
    <table>
        <tr>
            <td></td>
            <td>Special Topics Seminar</td>
            <td>2</td>
            <td>2</td>
            <td>2</td>
            <td>Elective</td>
            <td>Guest Speaker</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td>4 5</td>
            <td></td>
            <td></td>
            <td>Auditorium</td>
            <td>30</td>
            <td>0</td>
            <td>English</td>
            <td><a href="seminar.jsp">Link</a></td>
            <td>Open to all</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>
    """

    responses = {
        sem_url: dept_html,
        dept_url: dy_html,
        dy_url: course_html,
    }

    client = MockHTTPClient(responses=responses)
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) >= 1
    c = next((item for item in courses if item.name == "Special Topics Seminar"), None)
    assert c is not None
    assert c.code is None
    assert c.id == f"{current_roc_year}_{current_sem}_4010_Special Topics Seminar"


@pytest.mark.asyncio
async def test_bootstrap_sqlite_course_without_link(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Test course row where cell[18] has no <a> tag sets link to None."""
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=500"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=5010"

    dept_html = f'<a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=500">Dept</a>'
    dy_html = f'<a href="Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=5010">Year 1</a>'

    course_html = """
    <table>
        <tr>
            <td>500001</td>
            <td>No Link Course</td>
            <td>1</td>
            <td>1</td>
            <td>1</td>
            <td>Elective</td>
            <td>Instructor</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td>Room 202</td>
            <td>10</td>
            <td>0</td>
            <td>Chinese</td>
            <td>No link here</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>
    """

    responses = {
        sem_url: dept_html,
        dept_url: dy_html,
        dy_url: course_html,
    }

    client = MockHTTPClient(responses=responses)
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    c = next((item for item in courses if item.code == "500001"), None)
    assert c is not None
    assert c.link is None
