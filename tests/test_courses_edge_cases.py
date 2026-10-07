import logging
from datetime import date
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.initialize import DB
from app.core.models import Course, Department, DepartmentYear
from app.domains.courses.bootstrap_sqlite import bootstrap_sqlite
from tests.conftest import MockHTTPClient, MockRedis


# ---------------------------------------------------------------------------
# Passing Edge Cases (Handled properly by the source code)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_edge_case_empty_course_table_row(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Course scraping encounters empty <tr></tr> rows with 0 cells.

    Behavior: Handled gracefully via `if len(cells) == 0: continue`.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=100"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=1001"

    dept_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=100">Dept</a>'
    dy_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=1001">Class</a>'
    course_html = "<table><tr></tr><tr></tr></table>"

    client = MockHTTPClient(
        responses={sem_url: dept_html, dept_url: dy_html, dy_url: course_html}
    )
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) == 0


@pytest.mark.asyncio
async def test_edge_case_insufficient_cells_in_course_row(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Course scraping encounters malformed rows with fewer than 23 columns.

    Behavior: Handled gracefully via `except IndexError: continue`.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=200"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=2001"

    dept_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=200">Dept</a>'
    dy_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=2001">Class</a>'
    # Row with only 5 cells (e.g. subheader)
    course_html = "<table><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr></table>"

    client = MockHTTPClient(
        responses={sem_url: dept_html, dept_url: dy_html, dy_url: course_html}
    )
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) == 0


@pytest.mark.asyncio
async def test_edge_case_department_years_skips_error_tags(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Scraping department years returns <error> tags on network error.

    Behavior: Handled gracefully via `if department_year.name == 'error': continue`.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=300"

    dept_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=300">Dept</a>'

    client = MockHTTPClient(responses={sem_url: dept_html})
    # Make dept_url fail with HTTP 500 so scrape returns <error>
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_req = httpx.Request("GET", dept_url)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=mock_req, response=mock_resp
    )

    original_get = client.get

    async def custom_get(url):
        if url == dept_url:
            return mock_resp
        return await original_get(url)

    client.get = custom_get
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    # Department was saved, department years were skipped without unhandled crash
    depts = (await test_session.scalars(select(Department))).all()
    assert len(depts) >= 1
    dy_records = (await test_session.scalars(select(DepartmentYear))).all()
    assert len(dy_records) == 0


# ---------------------------------------------------------------------------
# Failing Edge Cases (Demonstrating bugs/flaws in existing source code)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug: bootstrap_sqlite accesses dep['href'] directly on line 100 without verifying 'href' attribute exists, raising KeyError",
    strict=True,
)
async def test_edge_case_department_anchor_without_href(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Department HTML contains <a> tags without an 'href' attribute (e.g. <a name="top">).

    Bug: Line 100 in bootstrap_sqlite.py accesses `dep['href']` instead of `dep.get('href')`.
    BeautifulSoup raises KeyError: 'href', causing the entire sync to abort.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"

    # HTML contains an <a> tag without href, followed by a valid department link
    dept_html = f"""
    <html>
        <body>
            <a name="top">Back to top</a>
            <a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=400">Computer Science</a>
        </body>
    </html>
    """

    client = MockHTTPClient(responses={sem_url: dept_html})
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    # If this bug didn't exist, the valid department would be saved into DB.
    # Currently, KeyError causes bootstrap_sqlite to abort and save 0 departments.
    await bootstrap_sqlite(ctx)

    depts = (await test_session.scalars(select(Department))).all()
    assert len(depts) >= 1, "Department should have been saved despite <a> without href"


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug: bootstrap_sqlite does not check if dep is <error> tag when scrape() fails, raising KeyError: 'href'",
    strict=True,
)
async def test_edge_case_department_scraping_network_error(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession, caplog
):
    """Edge Case: Network error when scraping departments for a semester.

    Bug: scrape() returns [<error></error>]. Unlike department_years (line 153),
    the department loop on line 100 does not check `if dep.name == 'error'`,
    causing `dep['href']` to raise KeyError: 'href' and aborting the entire sync.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"

    client = MockHTTPClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_req = httpx.Request("GET", sem_url)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "503 Service Unavailable", request=mock_req, response=mock_resp
    )
    client.get_mock.return_value = mock_resp

    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    with caplog.at_level(logging.ERROR):
        await bootstrap_sqlite(ctx)

    # In a bug-free implementation, network errors on individual semesters should be handled gracefully
    # without logging an unhandled sync failure caused by KeyError: 'href' on <error> tags.
    assert "NTUT -> DB sync failed" not in caplog.text
    assert "KeyError: 'href'" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug: bootstrap_sqlite does int() on cells[15]/cells[16] without catching ValueError if text is non-numeric (e.g. 'N/A' or '-')",
    strict=True,
)
async def test_edge_case_course_non_numeric_students_enrolled(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Course row contains non-numeric string in students_enrolled (cell 15) or students_dropped (cell 16).

    Bug: `int(cells[15].text.strip())` raises ValueError, which is NOT caught by `except IndexError: continue`.
    This causes the entire course sync loop to abort.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=600"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=6001"

    dept_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=600">Dept</a>'
    dy_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=6001">Class</a>'

    # Course row with "N/A" in cell 15 (students_enrolled)
    course_html = """
    <table>
        <tr>
            <td>600001</td>
            <td>Special Study</td>
            <td>3</td>
            <td>3</td>
            <td>3</td>
            <td>Elective</td>
            <td>Instructor</td>
            <td></td>
            <td>1 2 3</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td>Room 101</td>
            <td>N/A</td>
            <td>0</td>
            <td>Chinese</td>
            <td><a href="link.jsp">Link</a></td>
            <td>Notes</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>
    """

    client = MockHTTPClient(
        responses={sem_url: dept_html, dept_url: dy_html, dy_url: course_html}
    )
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) >= 1, "Course should have been saved even if enrolled is non-numeric"


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Bug: Course with both code and name empty produces name=None which violates NOT NULL constraint on Course.name",
    strict=True,
)
async def test_edge_case_course_empty_code_and_empty_name(
    test_db: DB, mock_redis: MockRedis, test_session: AsyncSession
):
    """Edge Case: Course row has empty string in both cell 0 (code) and cell 1 (name).

    Bug: Results in name=None, but models.py defines `name = Column(Unicode(255), nullable=False)`.
    During database commit, SQLAlchemy raises IntegrityError.
    """
    current_roc_year = date.today().year - 1911
    current_sem = 1 if date.today().month - 6 >= 0 else 2

    sem_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}"
    dept_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=700"
    dy_url = f"https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year={current_roc_year}&sem={current_sem}&code=7001"

    dept_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=700">Dept</a>'
    dy_html = f'<a href="Subj.jsp?year={current_roc_year}&sem={current_sem}&code=7001">Class</a>'

    # Course row with whitespace/empty for both code (cell 0) and name (cell 1)
    course_html = """
    <table>
        <tr>
            <td>   </td>
            <td>   </td>
            <td>3</td>
            <td>3</td>
            <td>3</td>
            <td>Elective</td>
            <td>Instructor</td>
            <td></td>
            <td>1 2 3</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td>Room 101</td>
            <td>20</td>
            <td>0</td>
            <td>Chinese</td>
            <td><a href="link.jsp">Link</a></td>
            <td>Notes</td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>
    """

    client = MockHTTPClient(
        responses={sem_url: dept_html, dept_url: dy_html, dy_url: course_html}
    )
    ctx = {"database": test_db, "redis": mock_redis, "client": client}

    await bootstrap_sqlite(ctx)

    courses = (await test_session.scalars(select(Course))).all()
    assert len(courses) >= 1
