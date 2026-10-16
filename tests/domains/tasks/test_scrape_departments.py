"""Unit tests for scrape_departments function in Tasks domain."""
from anyio import Path
from bs4 import BeautifulSoup
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.courses.schemas import DepartmentModel, SemesterModel
from app.domains.tasks.scrape.scrape_departments import scrape_departments


@pytest.mark.asyncio
async def test_scrape_departments_parsing_and_return_shape(tmp_path):
    """Test scrape_departments parses department links, extracts codes, deduplicates, and returns list[DepartmentModel]."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    html_content = """
    <html>
      <body>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=300">資訊工程系</a>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=42">電子工程系</a>
        <a href="Subj.jsp?format=-2&year=112&sem=1&code=300">資訊工程系重複</a>
        <a href="Subj.jsp?format=-2&year=112&sem=1">Invalid No Code</a>
      </body>
    </html>
    """
    soup = BeautifulSoup(html_content, "html.parser")
    mock_links = soup.find_all("a")

    ctx = {"client": AsyncMock()}
    sems = [
        SemesterModel(id="112_1", year="112", sem="1", link="Subj.jsp?year=112&sem=1")
    ]
    seen_dep_ids: set[str] = set()

    with patch(
        "app.domains.tasks.scrape.scrape_departments.scrape",
        new_callable=AsyncMock,
        return_value=mock_links,
    ):
        departments = await scrape_departments(
            ctx=ctx,
            parquet_dir=parquet_dir,
            sems_to_scrape=sems,
            seen_dep_ids=seen_dep_ids,
            chunk_size=10,
        )

    # 2 valid unique departments expected (300 and 042, with duplicate 300 and invalid link skipped)
    assert isinstance(departments, list)
    assert len(departments) == 2

    for d in departments:
        assert isinstance(d, DepartmentModel)
        assert d.semester_id == "112_1"
        assert d.year == "112"
        assert d.sem == "1"

    d1 = departments[0]
    assert d1.id == "112_1_300"
    assert d1.code == "300"
    assert d1.name == "資訊工程系"

    d2 = departments[1]
    assert d2.id == "112_1_042"
    assert d2.code == "042"
    assert d2.name == "電子工程系"

    # Verify seen_dep_ids mutated properly
    assert seen_dep_ids == {"112_1_300", "112_1_042"}


@pytest.mark.asyncio
async def test_scrape_departments_empty_semesters(tmp_path):
    """Test scrape_departments with empty semester list returns empty list."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    result = await scrape_departments(
        ctx={},
        parquet_dir=parquet_dir,
        sems_to_scrape=[],
        seen_dep_ids=set(),
    )
    assert result == []
