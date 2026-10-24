import datetime
import logging
import zoneinfo

from anyio import Path
from typing import Any, TypeVar
import uuid

import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import compute as pc
from pydantic import BaseModel

from app.domains.courses.schemas import (
    CourseModel,
    CourseSyllabusModel,
    DepartmentModel,
    DepartmentYearModel,
    SemesterModel,
)

logger: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

TABLE_MODEL_MAP: dict[str, type[BaseModel]] = {
    "semesters": SemesterModel,
    "departments": DepartmentModel,
    "department_years": DepartmentYearModel,
    "courses": CourseModel,
    "courses_syllabi": CourseSyllabusModel,
}


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    try:
        s = str(val).strip()
        return int(float(s)) if s else None
    except (ValueError, TypeError):
        return None


async def read_parquet_records(file_path: Path) -> list[dict[str, Any]]:
    """Reads a Parquet file and returns a list of raw row dictionaries."""
    if not await file_path.exists():
        return []
    return pq.read_table(file_path).to_pylist()


async def read_parquet_models(file_path: Path, model_cls: type[T]) -> list[T]:
    """Reads a Parquet file and returns a list of validated Pydantic model instances."""
    records = await read_parquet_records(file_path)
    return [model_cls.model_validate(r) for r in records]


async def append_to_parquet(
    table_name: str,
    new_records: list[SemesterModel] | list[DepartmentModel] | list[DepartmentYearModel] | list[CourseModel] | list[CourseSyllabusModel],
    parquet_dir: Path,
    compression: str = "snappy",
) -> Path:
    """Appends records to a Parquet file, validating against schema and deduplicating by 'id'."""
    file_path = parquet_dir / f"{table_name}.parquet"
    existing_records = await read_parquet_records(file_path)
    seen_ids: set[Any] = {r["id"] for r in existing_records if "id" in r}

    model_cls = TABLE_MODEL_MAP.get(table_name)
    combined: list[dict[str, Any]] = list(existing_records)

    for item in new_records:
        if isinstance(item, BaseModel):
            record_dict = item.model_dump()
        elif model_cls is not None:
            record_dict = model_cls.model_validate(item).model_dump()
        else:
            record_dict = dict(item)

        r_id = record_dict.get("id")
        if r_id is None or r_id not in seen_ids:
            row_copy = dict(record_dict)
            for k, v in row_copy.items():
                if hasattr(v, "isoformat"):
                    row_copy[k] = v.isoformat()
            combined.append(row_copy)
            if r_id is not None:
                seen_ids.add(r_id)

    if combined:
        # noinspection argument-list
        arrow_table = pa.Table.from_pylist(combined)
    else:
        # noinspection argument-list
        arrow_table = pa.Table.from_pydict({})

    pq.write_table(arrow_table, file_path, compression=compression)
    return file_path


async def write_parquet_chunk(
    table_name: str,
    new_records: list[SemesterModel] | list[DepartmentModel] | list[DepartmentYearModel] | list[CourseModel] | list[CourseSyllabusModel],
    parquet_dir: Path,
    chunk_id: int | str | None = None,
    compression: str = "snappy",
) -> Path:
    """Writes a chunk of records directly to a temporary parquet part file without reading existing files."""
    if not new_records:
        return parquet_dir / f"{table_name}.parquet"

    parts_dir = parquet_dir / f".{table_name}_parts"
    await parts_dir.mkdir(parents=True, exist_ok=True)

    part_name = f"part_{chunk_id if chunk_id is not None else uuid.uuid4().hex[:8]}.parquet"
    chunk_path = parts_dir / part_name

    model_cls = TABLE_MODEL_MAP.get(table_name)
    rows: list[dict[str, Any]] = []
    for item in new_records:
        if isinstance(item, BaseModel):
            record_dict = item.model_dump()
        elif model_cls is not None:
            record_dict = model_cls.model_validate(item).model_dump()
        else:
            record_dict = dict(item)

        row_copy = dict(record_dict)
        for k, v in row_copy.items():
            if hasattr(v, "isoformat"):
                row_copy[k] = v.isoformat()
        rows.append(row_copy)

    arrow_table = pa.Table.from_pylist(rows)
    pq.write_table(arrow_table, chunk_path, compression=compression)
    return chunk_path


async def consolidate_parquet_chunks(
    table_name: str,
    parquet_dir: Path,
    compression: str = "snappy",
) -> Path:
    """Consolidates temporary chunk part files (and any existing parquet file) into a final deduplicated parquet file."""
    parts_dir = parquet_dir / f".{table_name}_parts"
    final_file = parquet_dir / f"{table_name}.parquet"

    existing_records = await read_parquet_records(final_file) if await final_file.exists() else []
    seen_ids: set[Any] = {r["id"] for r in existing_records if "id" in r}
    combined: list[dict[str, Any]] = list(existing_records)

    if await parts_dir.exists():
        part_files = sorted([p async for p in parts_dir.glob("*.parquet")])
        for part_file in part_files:
            part_records = pq.read_table(part_file).to_pylist()
            for r in part_records:
                r_id = r.get("id")
                if r_id is None or r_id not in seen_ids:
                    combined.append(r)
                    if r_id is not None:
                        seen_ids.add(r_id)
            await part_file.unlink(missing_ok=True)
        try:
            await parts_dir.rmdir()
        except OSError:
            pass

    if combined:
        # noinspection argument-list
        arrow_table = pa.Table.from_pylist(combined)
    else:
        # noinspection argument-list
        arrow_table = pa.Table.from_pydict({})

    pq.write_table(arrow_table, final_file, compression=compression)
    return final_file


async def resolve_parquet_dir(ctx: dict[str, Any]) -> Path:
    """Resolves and ensures the parquet output directory exists."""
    if "parquet_dir" not in ctx:
        data_dir = (await Path(__file__).resolve()).parents[3] / "data"
        logger.info(f"DATA DIR: {data_dir}")
        parquet_dir = data_dir / "parquet"
        ctx["parquet_dir"] = parquet_dir
    else:
        parquet_dir = Path(ctx["parquet_dir"])
    await parquet_dir.mkdir(parents=True, exist_ok=True)
    return parquet_dir


def _coerce_timestamp_column(
    col: pa.ChunkedArray | pa.Array, now: datetime.datetime, tz: str | None = None
) -> pa.ChunkedArray | pa.Array:
    """Coerces a column to Arrow timestamp[us] (with or without timezone), filling nulls."""
    now_val = now if tz is not None else now.replace(tzinfo=None)
    now_scalar = pa.scalar(now_val, type=pa.timestamp(unit="us", tz=tz))

    if pa.types.is_string(col.type) or pa.types.is_large_string(col.type):
        if tz is not None:
            try:
                ts = pc.cast(col, pa.timestamp(unit="us", tz=tz))
            except Exception:
                ts_naive = pc.cast(col, pa.timestamp("us"))
                # pyrefly: ignore[missing-attribute]
                ts = pc.assume_timezone(ts_naive, tz)
        else:
            try:
                ts = pc.cast(col, pa.timestamp("us"))
            except Exception:
                ts_tz = pc.cast(col, pa.timestamp("us", tz="Asia/Taipei"))
                ts = pc.cast(ts_tz, pa.timestamp("us"))
    elif pa.types.is_timestamp(col.type):
        if tz is not None:
            # pyrefly: ignore[missing-attribute]
            ts = pc.assume_timezone(col, tz) if col.type.tz is None else pc.cast(col, pa.timestamp("us", tz=tz))
        else:
            ts = pc.cast(col, pa.timestamp("us"))
    else:
        ts = col

    return pc.fill_null(ts, now_scalar)


def _prepare_arrow_table(table: pa.Table, add_timestamps: bool = True) -> pa.Table:
    """Ensures timestamp columns are properly typed for SQL Server (DateTimeOffset vs DateTime) with no nulls."""
    now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Taipei"))
    for col_name in ("created_at", "updated_at"):
        if col_name in table.column_names:
            idx = table.schema.get_field_index(col_name)
            table = table.set_column(
                idx, col_name, _coerce_timestamp_column(table[col_name], now, tz="Asia/Taipei")
            )
        elif add_timestamps:
            ts_array = pa.array([now] * table.num_rows, type=pa.timestamp("us", tz="Asia/Taipei"))
            table = table.append_column(col_name, ts_array)

    if "last_updated" in table.column_names:
        idx = table.schema.get_field_index("last_updated")
        table = table.set_column(
            idx, "last_updated", _coerce_timestamp_column(table["last_updated"], now, tz=None)
        )

    return table
