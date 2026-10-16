"""Unit tests for parquet_utils in Tasks domain."""
from anyio import Path
import pyarrow as pa
import pytest

from app.domains.courses.schemas import SemesterModel
from app.domains.tasks.parquet_utils import (
    _prepare_arrow_table,
    _safe_int,
    append_to_parquet,
    consolidate_parquet_chunks,
    read_parquet_models,
    read_parquet_records,
    resolve_parquet_dir,
    write_parquet_chunk,
)


def test_safe_int_conversions():
    """Verify _safe_int correctly converts various input types."""
    assert _safe_int(123) == 123
    assert _safe_int("456") == 456
    assert _safe_int("789.0") == 789
    assert _safe_int("   42   ") == 42
    assert _safe_int(None) is None
    assert _safe_int("") is None
    assert _safe_int("not_a_number") is None


@pytest.mark.asyncio
async def test_resolve_parquet_dir(tmp_path):
    """Test resolve_parquet_dir creates and returns directory."""
    target_dir = Path(tmp_path / "custom_parquet")
    ctx = {"parquet_dir": target_dir}
    resolved = await resolve_parquet_dir(ctx)
    assert resolved == target_dir
    assert await target_dir.exists()


@pytest.mark.asyncio
async def test_append_and_read_parquet(tmp_path):
    """Test append_to_parquet writes records, deduplicates by id, and read functions parse models."""
    parquet_dir = Path(tmp_path / "parquet")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    sem1 = SemesterModel(id="112_1", year="112", sem="1", link="link1")
    sem2 = SemesterModel(id="112_2", year="112", sem="2", link="link2")

    # 1. Write initial 2 records
    file_path = await append_to_parquet("semesters", [sem1, sem2], parquet_dir)
    assert await file_path.exists()

    # 2. Read back as raw records
    raw_records = await read_parquet_records(file_path)
    assert len(raw_records) == 2
    assert raw_records[0]["id"] == "112_1"
    assert raw_records[1]["id"] == "112_2"

    # 3. Read back as validated models
    models = await read_parquet_models(file_path, SemesterModel)
    assert len(models) == 2
    assert isinstance(models[0], SemesterModel)
    assert models[0].id == "112_1"

    # 4. Append duplicate sem1 and new sem3
    sem3 = SemesterModel(id="113_1", year="113", sem="1", link="link3")
    await append_to_parquet("semesters", [sem1, sem3], parquet_dir)

    updated_models = await read_parquet_models(file_path, SemesterModel)
    # Total should be 3 unique records (sem1, sem2, sem3)
    assert len(updated_models) == 3
    ids = [m.id for m in updated_models]
    assert ids == ["112_1", "112_2", "113_1"]


@pytest.mark.asyncio
async def test_write_and_consolidate_chunks(tmp_path):
    """Test write_parquet_chunk writes temporary parts and consolidate_parquet_chunks merges them."""
    parquet_dir = Path(tmp_path / "parquet_chunks")
    await parquet_dir.mkdir(parents=True, exist_ok=True)

    c1 = SemesterModel(id="sem_1", year="110", sem="1", link="l1")
    c2 = SemesterModel(id="sem_2", year="110", sem="2", link="l2")
    c3 = SemesterModel(id="sem_1", year="110", sem="1", link="l1_dup")
    c4 = SemesterModel(id="sem_3", year="111", sem="1", link="l3")

    # Write chunk 1
    part1 = await write_parquet_chunk("semesters", [c1, c2], parquet_dir, chunk_id=1)
    assert await part1.exists()

    # Write chunk 2
    part2 = await write_parquet_chunk("semesters", [c3, c4], parquet_dir, chunk_id=2)
    assert await part2.exists()

    # Consolidate
    final_file = await consolidate_parquet_chunks("semesters", parquet_dir)
    assert await final_file.exists()

    records = await read_parquet_records(final_file)
    assert len(records) == 3
    assert {r["id"] for r in records} == {"sem_1", "sem_2", "sem_3"}

    # Temporary directory should be cleaned up
    parts_dir = parquet_dir / ".semesters_parts"
    assert not await parts_dir.exists()


def test_prepare_arrow_table_timestamps():
    """Test _prepare_arrow_table adds created_at and updated_at with timezone."""
    table = pa.Table.from_pydict({"id": ["1", "2"], "name": ["A", "B"]})
    prepared = _prepare_arrow_table(table, add_timestamps=True)

    assert "created_at" in prepared.column_names
    assert "updated_at" in prepared.column_names
    assert prepared.schema.field("created_at").type == pa.timestamp("us", tz="Asia/Taipei")
    assert prepared.schema.field("updated_at").type == pa.timestamp("us", tz="Asia/Taipei")
