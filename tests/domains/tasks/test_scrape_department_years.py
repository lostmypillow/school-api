"""Unit tests for scrape_department_years function in Tasks domain."""
from anyio import Path
from bs4 import BeautifulSoup
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.courses.schemas import DepartmentModel, DepartmentYearModel
from app.domains.tasks.scrape.scrape_department_years import scrape_department_years


@pytest.mark.asyncio
async def test_scrape_department_years_parsing_and_return_shape(tmp_path):
    """Test scrape_department_years parses cohort links, handles skips, and returns list[DepartmentYearModel]."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    html_content = """
    <html>
      <body>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=101">資工一年級</a>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=2">資工二年級</a>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=101">重複的一年級</a>
        <error href="Subj.jsp?format=-2&year=112&sem=1&code=999">Error Tag</error>
        <a>No Href Link</a>
        <a href="other.jsp">Invalid Regex Link</a>
      </body>
    </html>
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # All tags inside body
    mock_tags = soup.body.find_all(True)

    ctx = {"client": AsyncMock()}
    depts = [
        DepartmentModel(
            id="112_1_300",
            semester_id="112_1",
            year="112",
            sem="1",
            code="300",
            name="資訊工程系",
            link="Subj.jsp?year=112&sem=1&code=300",
        )
    ]
    seen_class_ids: set[str] = set()

    with patch(
        "app.domains.tasks.scrape.scrape_department_years.scrape",
        new_callable=AsyncMock,
        return_value=mock_tags,
    ):
        result = await scrape_department_years(
            ctx=ctx,
            parquet_dir=parquet_dir,
            departments_to_scrape=depts,
            seen_class_ids=seen_class_ids,
            chunk_size=10,
        )

    assert isinstance(result, list)
    assert len(result) == 2

    for dy in result:
        assert isinstance(dy, DepartmentYearModel)
        assert dy.department_id == "112_1_300"
        assert dy.year == "112"
        assert dy.sem == "1"

    dy1 = result[0]
    assert dy1.id == "112_1_300_0101"
    assert dy1.code == "0101"
    assert dy1.name == "資工一年級"

    dy2 = result[1]
    assert dy2.id == "112_1_300_0002"
    assert dy2.code == "0002"
    assert dy2.name == "資工二年級"

    assert seen_class_ids == {"112_1_300_0101", "112_1_300_0002"}


@pytest.mark.asyncio
async def test_scrape_department_years_empty(tmp_path):
    """Test scrape_department_years with empty input returns empty list."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    result = await scrape_department_years(
        ctx={},
        parquet_dir=parquet_dir,
        departments_to_scrape=[],
        seen_class_ids=set(),
    )
    assert result == []
