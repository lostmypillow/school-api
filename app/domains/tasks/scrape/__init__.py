from .main import (
    read_parquet_models,
    scrape_courses,
    scrape_department_years,
    scrape_departments,
    scrape_to_parquet,
    sync_semesters,
)
from app.domains.tasks.parquet_utils import (_safe_int,
                                             append_to_parquet,
                                             consolidate_parquet_chunks)
from ..scrape_utils import fetch_html

__all__ = [
    "scrape_to_parquet",
    "append_to_parquet",
    "consolidate_parquet_chunks",
    "read_parquet_models",
    "_safe_int",
    "sync_semesters.py",
    "sync_semesters",
    "scrape_departments",
    "scrape_department_years",
    "scrape_courses",
]