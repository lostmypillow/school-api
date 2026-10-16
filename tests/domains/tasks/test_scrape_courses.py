from pathlib import Path
from typing import Any

import httpx
import pytest
import pytest_asyncio

from app.core.custom_http_client import CustomAsyncClient
from app.domains.courses.schemas import CourseModel, DepartmentYearModel
from app.domains.tasks.scrape.scrape_courses import parse_course_row, scrape_courses
from app.domains.tasks.parquet_utils import read_parquet_records

PARQUET_SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "data" / "parquet"


@pytest_asyncio.fixture
async def live_client():
    """Provides a live CustomAsyncClient targeting NTUT course catalog with SSL verification disabled."""
    client = CustomAsyncClient(
        verify=False,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
        timeout=30.0,
    )
    try:
        yield client
    finally:
        if not client.is_closed:
            await client.aclose()


def test_parse_course_row_empty():
    """Tests parse_course_row returns None on an empty course row."""
    parent = DepartmentYearModel(
        id="113_1_001_0482",
        department_id="113_1_001",
        year="113",
        sem="1",
        code="0482",
        name="跨校選課",
        link="link",
    )
    assert parse_course_row("<tr></tr>", parent) is None


def test_parse_course_row_valid():
    """Tests parse_course_row parses a valid table row with course cells into CourseModel."""
    parent = DepartmentYearModel(
        id="113_1_001_0482",
        department_id="113_1_001",
        year="113",
        sem="1",
        code="0482",
        name="跨校選課",
        link="link",
    )
    cells = [
        "<td>300101</td>",  # 0: code
        "<td>計算機概論</td>",  # 1: name
        "<td>3</td>",  # 2: credits
        "<td></td>",  # 3
        "<td></td>",  # 4
        "<td>必修</td>",  # 5: course_type
        "<td>王小明</td>",  # 6: instructor
        "<td></td>",  # 7: sun
        "<td>1-3</td>",  # 8: mon
        "<td></td>",  # 9: tue
        "<td></td>",  # 10: wed
        "<td></td>",  # 11: thu
        "<td></td>",  # 12: fri
        "<td></td>",  # 13: sat
        "<td>綜合科館415</td>",  # 14: classroom
        "<td>50</td>",  # 15: students_enrolled
        "<td>2</td>",  # 16: students_dropped
        "<td>中文</td>",  # 17: language
        "<td><a href='ShowSyllabus.jsp?snum=123'>大綱</a></td>",  # 18: link
        "<td>備註文字</td>",  # 19: notes
        "<td></td>",  # 20: with_class
        "<td></td>",  # 21: experiment
        "<td></td>",  # 22: cross_discipline
    ]
    tr_html = f"<tr>{''.join(cells)}</tr>"
    course = parse_course_row(tr_html, parent)
    assert course is not None
    assert isinstance(course, CourseModel)
    assert course.code == "300101"
    assert course.name == "計算機概論"
    assert course.credits == 3
    assert course.instructor == "王小明"
    assert course.classroom == "綜合科館415"
    assert course.students_enrolled == 50
    assert course.link == "ShowSyllabus.jsp?snum=123"


@pytest.mark.asyncio
async def test_scrape_courses_real_url(
    live_client: CustomAsyncClient,
    temp_parquet_dir: Path,
):
    """Step 4: Test that courses can be scraped and saved via scrape_courses."""
    ctx = {"client": live_client}
    parquet_path = PARQUET_SNAPSHOT_DIR / "department_years.parquet"

    # Retrieve an example department_year from department_years.parquet snapshot
    sample_dy: dict[str, Any] = {}
    if parquet_path.exists():
        dy_records = read_parquet_records(parquet_path)
        sample_dy = next(
            (
                dy for dy in dy_records
                if dy.get("year") in ("113", "112") and "code=482" in dy.get("link", "")
            ),
            dy_records[0] if dy_records else {},
        )

    dy_year = sample_dy.get("year", "113")
    dy_sem = sample_dy.get("sem", "1")
    dy_code = sample_dy.get("code", "0482")
    dy_name = sample_dy.get("name", "跨校選課(大)")
    dy_link = sample_dy.get("link") or f"Subj.jsp?format=-4&year={dy_year}&sem={dy_sem}&code=482"
    dy_id = sample_dy.get("id", f"{dy_year}_{dy_sem}_001_{dy_code}")
    parent_dep_year = DepartmentYearModel(
        id=dy_id,
        department_id=sample_dy.get("department_id", f"{dy_year}_{dy_sem}_001"),
        year=dy_year,
        sem=dy_sem,
        code=dy_code,
        name=dy_name,
        link=dy_link,
    )

    print(f"\n[STEP 4: Input] Scraping courses for: {dy_name} via real URL: {dy_link}")

    course_list = await scrape_courses(
        ctx=ctx,
        parquet_dir=temp_parquet_dir,
        dep_years_to_scrape=[parent_dep_year],
        chunk_size=1,
    )
    assert len(course_list) > 0, f"Expected courses parsed from {dy_link}, got 0"

    # Validate output written to parquet
    parquet_file = temp_parquet_dir / "courses.parquet"
    assert parquet_file.exists(), "courses.parquet should have been created"
    saved_records = read_parquet_records(parquet_file)
    assert len(saved_records) == len(course_list)

    # Validate each course with Pydantic CourseModel
    validated_courses: list[CourseModel] = []
    for c in course_list:
        model = CourseModel.model_validate(c)
        validated_courses.append(model)

    print("\n" + "=" * 70)
    print(f"[STEP 4: Courses] Scraped and validated {len(validated_courses)} courses for {dy_name} ({dy_link}):")
    for c in validated_courses[:5]:
        print(
            f"  - [{c.code}] {c.name} | credits: {c.credits} | "
            f"instructor: {c.instructor or 'N/A'} | link: {c.link}"
        )
    if len(validated_courses) > 5:
        print(f"  ... and {len(validated_courses) - 5} more courses.")
    print("=" * 70)

    assert len(validated_courses) > 0
    assert any(c.name is not None for c in validated_courses)
    assert any(c.credits is not None for c in validated_courses)
