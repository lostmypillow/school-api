import asyncio
import hashlib
import random

from anyio import Path, to_thread
import polars as pl
SCHOOLS = [
    "國立臺灣科技大學",
    "國立雲林科技大學",
    "國立屏東科技大學",
    "國立臺北科技大學",
    "國立虎尾科技大學",
    "國立澎湖科技大學",
    "國立勤益科技大學",
    "國立臺北護理健康大學",
    "國立高雄餐旅大學",
    "國立臺中科技大學",
    "國立臺北商業大學",
    "國立高雄科技大學",
    "國立臺灣戲曲學院",
    "國立臺南護理專科學校",
    "國立臺東專科學校",
]


def _sync_employees_worker(base_path: Path) -> None:
    """Memory & CPU optimized Polars worker running lazy query plan."""

    syllabi_lf = pl.scan_parquet(str(base_path / "courses_syllabi.parquet"))

    courses_lf = pl.scan_parquet(str(base_path / "courses.parquet")).select(
        ["id", "department_year_id"]
    )

    dept_years_lf = pl.scan_parquet(
        str(base_path / "department_years.parquet")
    ).select(["id", "department_id"])

    departments_lf = pl.scan_parquet(
        str(base_path / "departments.parquet")
    ).select(["id", "code"])

    enriched_lf = (
        syllabi_lf.join(courses_lf, left_on="course_id", right_on="id", how="left")
        .join(dept_years_lf, left_on="department_year_id", right_on="id", how="left")
        .join(
            departments_lf.rename({"code": "department_code"}),
            left_on="department_id",
            right_on="id",
            how="left",
        )
    )

    cols = ["instructor_name", "email", "department_code"]

    selected_school = random.choice(SCHOOLS)

    instructors_lf = (
        enriched_lf.select(
            *cols,
            pl.lit(selected_school).alias("college"),
        )
        .rename({"instructor_name": "name", "department_code": "department"})
        .drop_nulls()
        .sort(["name", "email", "department"])
        .unique(subset=["name"], keep="first")
        .unique(subset=["email"], keep="first")
        .with_row_index(name="row_num", offset=100000)
        .with_columns(
            pl.col("row_num").cast(pl.String).alias("id"),
            pl.concat_str(exprs=[pl.col("name"), pl.col("email")], separator=":")
            .map_elements(
                lambda val: hashlib.sha256(val.encode("utf-8")).hexdigest()[:20],
                return_dtype=pl.String,
            )
            .alias("card_id"),
            pl.lit(None).cast(pl.String).alias("new_college"),
        )
        .drop("row_num")
        .select(
            ["id", "name", "card_id", "college", "new_college", "department", "email"]
        )
    )
    df = instructors_lf.collect()

    duplicates = df.filter(pl.col("id").is_duplicated())
    if not duplicates.is_empty():
        print("DUPLICATES FOUND:")
        print(duplicates)

    output_path = base_path / "employees.parquet"

    df.write_parquet(str(output_path))

    print("Done")
    print(
        pl.read_parquet(str(output_path)).row(
            random.randint(0, min(100, len(df) - 1)), named=True
        )
    )

async def sync_employees() -> None:
    """Async wrapper that offloads heavy lazy Polars computation to thread pool."""
    base_path = Path(__file__).parents[5] / "data" / "parquet"
    await to_thread.run_sync(_sync_employees_worker, base_path)


if __name__ == "__main__":
    asyncio.run(sync_employees())
    