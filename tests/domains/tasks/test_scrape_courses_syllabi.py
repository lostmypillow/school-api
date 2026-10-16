"""Unit tests for parse_course_syllabus in Tasks domain."""
from bs4 import BeautifulSoup
import pytest
from unittest.mock import AsyncMock

from app.domains.courses.schemas import CourseModel, CourseSyllabusModel
from app.domains.tasks.scrape.scrape_courses_syllabi import (
    parse_course_syllabus,
    parse_courses_syllabi_row,
)


@pytest.fixture
def sample_course() -> CourseModel:
    return CourseModel(
        id="112_1_101_300001",
        department_year_id="112_1_300_101",
        year="112",
        sem="1",
        code="300001",
        name="演算法",
    )


@pytest.mark.asyncio
async def test_parse_course_syllabus_full_fields(sample_course: CourseModel):
    """Test parse_course_syllabus maps all table fields and sets exact CourseSyllabusModel shape."""
    html_doc = """
    <table>
      <tr><th>教師姓名</th><td>王正豪教師諮商時間</td></tr>
      <tr><th>Email</th><td>jhwang@ntut.edu.tw</td></tr>
      <tr><th>課程大綱</th><td>本課程介紹演算法分析與設計技巧。</td></tr>
      <tr><th>課程進度(1-16週)</th><td>第1週: 漸近符號，第2週: 分治法</td></tr>
      <tr><th>評量方式與標準</th><td>期中考 40%, 期末考 40%, 作業 20%</td></tr>
      <tr><th>使用教材、參考書目或其他</th><td>Introduction to Algorithms (CLRS)</td></tr>
      <tr><th>課程諮詢管道</th><td>每週二 14:00-16:00 於科研大樓 402</td></tr>
      <tr><th>課程是否導入AI</th><td>可作為輔助工具，需附上提示詞與產出摘要</td></tr>
      <tr><th>備註</th><td>請務必攜帶筆電上課</td></tr>
      <tr><th>課程對應SDGs指標</th><td>優質教育 (SDG 4)</td></tr>
    </table>
    """
    soup = BeautifulSoup(html_doc, "html.parser")
    tr_elements = soup.find_all("tr")

    ctx = {"client": AsyncMock()}
    result = await parse_course_syllabus(
        ctx=ctx,
        tr_elements=tr_elements,
        course=sample_course,
    )

    assert result is not None
    assert isinstance(result, CourseSyllabusModel)
    assert result.id == "112_1_101_300001_syllabus"
    assert result.course_id == "112_1_101_300001"
    assert result.instructor_name == "王正豪"
    assert result.email == "jhwang@ntut.edu.tw"
    assert result.abstract == "本課程介紹演算法分析與設計技巧。"
    assert result.syllabus == "第1週: 漸近符號，第2週: 分治法"
    assert result.grading_policy == "期中考 40%, 期末考 40%, 作業 20%"
    assert result.materials == "Introduction to Algorithms (CLRS)"
    assert result.consultation == "每週二 14:00-16:00 於科研大樓 402"
    assert result.ai == "可作為輔助工具，需附上提示詞與產出摘要"
    assert result.notes == "請務必攜帶筆電上課"
    assert result.sdg == "優質教育 (SDG 4)"


@pytest.mark.asyncio
async def test_parse_course_syllabus_with_schedule_map(sample_course: CourseModel):
    """Test parse_course_syllabus extracts instructor_schedule via schedule_map."""
    html_doc = """
    <table>
      <tr><th>教師姓名</th><td>王正豪</td></tr>
      <tr>
        <th align="left">
          <a href="TeacherSchedule.jsp?tid=123">課表</a>
        </th>
      </tr>
    </table>
    """
    soup = BeautifulSoup(html_doc, "html.parser")
    tr_elements = soup.find_all("tr")

    schedule_map = {"TeacherSchedule.jsp?tid=123": "星期一 09:00-12:00\n星期三 13:00-15:00"}
    ctx = {"client": AsyncMock()}

    result = await parse_course_syllabus(
        ctx=ctx,
        tr_elements=tr_elements,
        course=sample_course,
        schedule_map=schedule_map,
    )

    assert result is not None
    assert result.instructor_schedule == "星期一 09:00-12:00\n星期三 13:00-15:00"


@pytest.mark.asyncio
async def test_parse_course_syllabus_empty_returns_none(sample_course: CourseModel):
    """Test parse_course_syllabus with no matched fields returns None."""
    html_doc = "<table><tr><td>Random Unmatched Data</td></tr></table>"
    soup = BeautifulSoup(html_doc, "html.parser")
    tr_elements = soup.find_all("tr")

    result = await parse_courses_syllabi_row(
        ctx={},
        tr_elements=tr_elements,
        course=sample_course,
    )
    assert result is None
