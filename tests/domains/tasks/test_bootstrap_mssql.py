"""Unit and integration tests for bootstrap_mssql in Tasks domain."""
import os
import socket
from anyio import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.tasks.bootstrap_mssql.main import bootstrap_mssql
from app.domains.tasks.bootstrap_mssql.schemas import BootstrapSummaryModel


# ==============================================================================
# Unit Tests (Mocked DB)
# ==============================================================================


@pytest.mark.asyncio
async def test_bootstrap_mssql_unit_summary_shape(tmp_path):
    """Test bootstrap_mssql executes migration sequence and returns exact BootstrapSummaryModel dictionary shape."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy parquet files
    sem_table = pa.Table.from_pydict({"id": ["112_1"], "year": ["112"], "sem": ["1"], "link": ["link"]})
    pq.write_table(sem_table, parquet_dir / "semesters.parquet")

    dept_table = pa.Table.from_pydict({
        "id": ["112_1_300"], "semester_id": ["112_1"], "year": ["112"], "sem": ["1"],
        "code": ["300"], "name": ["CS"], "link": ["link"]
    })
    pq.write_table(dept_table, parquet_dir / "departments.parquet")

    dy_table = pa.Table.from_pydict({
        "id": ["112_1_300_101"], "department_id": ["112_1_300"], "year": ["112"], "sem": ["1"],
        "code": ["101"], "name": ["Year 1"], "link": ["link"]
    })
    pq.write_table(dy_table, parquet_dir / "department_years.parquet")

    course_table = pa.Table.from_pydict({
        "id": ["c1"], "department_year_id": ["112_1_300_101"], "year": ["112"], "sem": ["1"],
        "name": ["Algorithms"]
    })
    pq.write_table(course_table, parquet_dir / "courses.parquet")

    syl_table = pa.Table.from_pydict({
        "id": ["s1"], "course_id": ["c1"], "instructor_name": ["Turing"]
    })
    pq.write_table(syl_table, parquet_dir / "courses_syllabi.parquet")

    ctx = {"parquet_dir": parquet_dir}

    with patch(
        "app.domains.tasks.bootstrap_mssql.main.exec_mssql_async",
        new_callable=AsyncMock,
    ) as mock_exec:
        summary = await bootstrap_mssql(ctx=ctx)

    # 1. Assert return value strictly satisfies BootstrapSummaryModel
    validated = BootstrapSummaryModel.model_validate(summary)
    assert validated.semesters == 1
    assert validated.departments == 1
    assert validated.department_years == 1
    assert validated.courses == 1
    assert validated.courses_syllabi == 1

    # 2. Assert exact dictionary keys
    assert set(summary.keys()) == {
        "semesters",
        "departments",
        "department_years",
        "courses",
        "courses_syllabi",
    }

    # 3. Assert initial DB and schema bootstrap steps executed
    mock_exec.assert_any_await(command_name="create_database")
    mock_exec.assert_any_await(command_name="create_tables")
    mock_exec.assert_any_await(command_name="tutors/bootstrap_tutor", fetch=False)


# ==============================================================================
# Integration Test (Against Live MSSQL)
# ==============================================================================

MSSQL_HOST = os.getenv("TEST_MSSQL_HOST", "127.0.0.1")
MSSQL_PORT = int(os.getenv("TEST_MSSQL_PORT", "1433"))


def is_mssql_reachable() -> bool:
    try:
        with socket.create_connection((MSSQL_HOST, MSSQL_PORT), timeout=1.5):
            return True
    except OSError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not is_mssql_reachable(),
    reason=f"MSSQL not reachable at {MSSQL_HOST}:{MSSQL_PORT}",
)
@pytest.mark.asyncio
async def test_bootstrap_mssql_integration_real_db(tmp_path):
    """Test bootstrap_mssql against live MSSQL container with real bulk copy."""
    parquet_dir = Path(tmp_path / "parquet_live")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    # Create 1 semester record
    sem_table = pa.Table.from_pydict({
        "id": ["999_1"], "year": ["999"], "sem": ["1"], "link": ["http://test"]
    })
    pq.write_table(sem_table, parquet_dir / "semesters.parquet")

    ctx = {"parquet_dir": parquet_dir}
    summary = await bootstrap_mssql(ctx=ctx)

    validated = BootstrapSummaryModel.model_validate(summary)
    assert validated.semesters == 1
    assert validated.departments == 0
