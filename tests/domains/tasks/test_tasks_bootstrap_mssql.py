from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.tasks.bootstrap_mssql import main
from app.domains.tasks.scrape import append_to_parquet


@pytest.mark.asyncio
async def test_bootstrap_mssql_empty_parquet(temp_parquet_dir: Path):
    """Test bootstrap_mssql returns 0 counts when no parquet files exist."""
    ctx = {"parquet_dir": temp_parquet_dir}
    with patch(
            "app.domains.tasks.bootstrap_mssql.main.py.py.exec_mssql_async", new_callable=AsyncMock
    ) as mock_exec:
        summary = await main(ctx)

        assert summary["semesters"] == 0
        assert summary["departments"] == 0
        assert summary["department_years"] == 0
        assert summary["courses"] == 0
        assert mock_exec.await_count == 3
        commands_called = [call.args[0] for call in mock_exec.await_args_list]
        assert "create_database" in commands_called
        assert "create_tables" in commands_called
        assert "tutors/bootstrap_tutor" in commands_called


@pytest.mark.asyncio
async def test_bootstrap_mssql_full_pipeline(temp_parquet_dir: Path):
    """Test bootstrap_mssql reads parquet files and calls exec_mssql_async for all tables."""
    sem_records = [
        {"id": "112_1", "year": "112", "sem": "1", "link": "Subj.jsp?year=112&sem=1"}
    ]
    dept_records = [
        {
            "id": "112_1_300",
            "semester_id": "112_1",
            "year": "112",
            "sem": "1",
            "code": "300",
            "name": "Computer Science",
            "link": "Subj.jsp?year=112&sem=1&code=300",
        }
    ]
    dy_records = [
        {
            "id": "112_1_300_101",
            "department_id": "112_1_300",
            "year": "112",
            "sem": "1",
            "code": "101",
            "name": "CS Year 1",
            "link": "Subj.jsp?year=112&sem=1&code=101",
        }
    ]
    course_records = [
        {
            "id": "112_1_101_300001",
            "department_year_id": "112_1_300_101",
            "year": "112",
            "sem": "1",
            "code": "300001",
            "name": "Data Structures",
            "link": "syllabus.jsp?id=300001",
            "credits": 3,
            "course_type": "Required",
            "instructor": "Prof Turing",
            "sun": None,
            "mon": "1 2 3",
            "tue": None,
            "wed": None,
            "thu": None,
            "fri": None,
            "sat": None,
            "classroom": "Room 101",
            "students_enrolled": 40,
            "students_dropped": 0,
            "language": "Chinese",
            "notes": None,
            "with_class": None,
            "experiment": None,
            "cross_discipline": None,
        }
    ]

    await append_to_parquet(table_name="semesters", new_records=sem_records, parquet_dir=temp_parquet_dir)
    await append_to_parquet(table_name="departments", new_records=dept_records, parquet_dir=temp_parquet_dir)
    await append_to_parquet(table_name="department_years", new_records=dy_records, parquet_dir=temp_parquet_dir)
    await append_to_parquet(table_name="courses", new_records=course_records, parquet_dir=temp_parquet_dir)

    ctx = {"parquet_dir": temp_parquet_dir}

    with patch(
            target="app.domains.tasks.bootstrap_mssql.main.py.py.exec_mssql_async", new_callable=AsyncMock
    ) as mock_exec:
        summary = await main(ctx)

        assert summary["semesters"] == 1
        assert summary["departments"] == 1
        assert summary["department_years"] == 1
        assert summary["courses"] == 1

        assert mock_exec.await_count == 7
        commands_called = [call.args[0] for call in mock_exec.await_args_list]
        assert "create_database" in commands_called
        assert "create_tables" in commands_called
        assert "tutors/bootstrap_tutor" in commands_called
        assert "courses/upsert_semester" in commands_called
        assert "courses/upsert_department" in commands_called
        assert "courses/upsert_department_year" in commands_called
        assert "courses/upsert_course" in commands_called


@pytest.mark.asyncio
async def test_bootstrap_mssql_large_dataset_batching(temp_parquet_dir: Path):
    """Test bootstrap_mssql processes records in batches when exceeding 5000 rows."""
    sem_records = [
        {
            "id": f"sem_{i}",
            "year": f"Y{i}",
            "sem": "1",
            "link": f"link_{i}",
        }
        for i in range(5010)
    ]
    await append_to_parquet("semesters", sem_records, temp_parquet_dir)

    ctx = {"parquet_dir": temp_parquet_dir}

    with patch(
            "app.domains.tasks.bootstrap_mssql.main.py.py.exec_mssql_async", new_callable=AsyncMock
    ) as mock_exec:
        summary = await main(ctx)
        assert summary["semesters"] == 5010
        mock_exec.assert_awaited()
