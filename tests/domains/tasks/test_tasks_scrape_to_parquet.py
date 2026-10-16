from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from app.core.custom_http_client import CustomAsyncClient
from app.domains.courses.schemas import (
    CourseModel,
    DepartmentModel,
    DepartmentYearModel,
    SemesterModel,
)
from app.domains.tasks.scrape import (
    read_parquet_records,
    scrape_to_parquet,
)


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


@pytest.mark.asyncio
async def test_scrape_to_parquet_entire_function(
    live_client: CustomAsyncClient,
    temp_parquet_dir: Path,
):
    """Tests the entire scrape_to_parquet function with a real semester year.

    Uses a disposable parquet directory (temp_parquet_dir) so prod parquet data
    in data/parquet is not disturbed.
    """

    ctx = {
        "parquet_dir": temp_parquet_dir,
        "client": live_client,
    }

    # Run the entire scrape_to_parquet function for the specified real semester year
    await scrape_to_parquet(ctx=ctx)

    # 1. Verify semesters.parquet created and contains valid records
    sem_file = temp_parquet_dir / "semesters.parquet"
    assert sem_file.exists(), "semesters.parquet should exist in disposable dir"
    sem_records = read_parquet_records(sem_file)
    assert len(sem_records) > 0, "Expected semester records in disposable parquet"
    for r in sem_records:
        SemesterModel.model_validate(r)

    # 2. Verify departments.parquet created and contains valid records
    dept_file = temp_parquet_dir / "departments.parquet"
    assert dept_file.exists(), "departments.parquet should exist in disposable dir"
    dept_records = read_parquet_records(dept_file)
    assert len(dept_records) > 0, "Expected department records in disposable parquet"
    for r in dept_records:
        DepartmentModel.model_validate(r)

    # 3. Verify department_years.parquet created and contains valid records
    dy_file = temp_parquet_dir / "department_years.parquet"
    assert dy_file.exists(), "department_years.parquet should exist in disposable dir"
    dy_records = read_parquet_records(dy_file)
    assert len(dy_records) > 0, "Expected department year records in disposable parquet"
    for r in dy_records:
        DepartmentYearModel.model_validate(r)

    # 4. Verify courses.parquet created and contains valid records
    course_file = temp_parquet_dir / "courses.parquet"
    assert course_file.exists(), "courses.parquet should exist in disposable dir"
    course_records = read_parquet_records(course_file)
    assert len(course_records) > 0, "Expected course records in disposable parquet"
    for r in course_records:
        CourseModel.model_validate(r)


# @pytest.mark.asyncio
# async def test_scrape(live_client: CustomAsyncClient, capsys: CaptureFixture[str]):
#     ctx = {"client": live_client}
#     url = "/ShowSyllabus.jsp?snum=354648&code=11297"
#     result = await scrape(ctx=ctx, url=url, tag="tr")
#     conversion_dict = {
#         "教師姓名": "instructor_name",
#         "最後更新時間": "last_updated",
#         "評量方式與標準": "grading_policy",
#         "備註": "notes",
#         "使用教材、參考書目或其他": "materials",
#         "Email": "email",
#         "課程大綱": "abstract",
#         "課程是否導入AI": "ai",
#         "課程諮詢管道": "consultation",
#         "課程對應SDGs指標": "sdg",
#         "課程進度(1-16週)": "syllabus",
#         "課程進度": "syllabus"
#     }
#     parsed_result = {}
#     instructor_schedule = ''
#     for idx, x in enumerate(result):
#         soup = BeautifulSoup(str(x), features="html.parser")
#         scrape_key = soup.find(name="th")
#         key = scrape_key.get_text(strip=True).strip() if scrape_key else ""
#         scrape_value = soup.find(name="td")
#         href = None
#
#         if not scrape_value:
#             scrape_value = soup.find(name="th", align="left")
#             a_tag = soup.find("a")
#             href = a_tag.get("href") if a_tag else ""
#             if href and not href.startswith("mailto") :
#                 res = await scrape(ctx=ctx, url=href, tag="body")
#                 res_list = str(res).strip().split("<br/>")
#                 for res_idx, r in enumerate[str](res_list):
#                     instructor_schedule += '\n'
#                     if r.strip().startswith("星期"):
#                         instructor_schedule += f"{r.strip().replace('\u3000', ' ')}"
#
#
#         value = scrape_value.get_text(separator="\n", strip=True).strip() if scrape_value else ""
#         value = value.split("教師諮商時間")[0].strip()
#         soup.decompose()
#         if key != "" and value != "":
#             parsed_result[key] = value.strip()
#     if instructor_schedule != '':
#         parsed_result["instructor_schedule"] = instructor_schedule
#
#     renamed_data = {conversion_dict.get(k, k): v.strip() for k, v in parsed_result.items()}
#     pprint(renamed_data, indent=4)
#
#     assert False

