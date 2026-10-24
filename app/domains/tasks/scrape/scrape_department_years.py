import asyncio
from itertools import batched
import math
from anyio import Path
import re
from typing import Any

from tqdm.auto import tqdm

from app.domains.courses.schemas import DepartmentModel, DepartmentYearModel
from app.domains.tasks.parquet_utils import append_to_parquet
from app.domains.tasks.scrape_utils import scrape


async def scrape_department_years(
    ctx: dict[str, Any],
    parquet_dir: Path,
    departments_to_scrape: list[DepartmentModel] | list[dict[str, Any]],
    seen_class_ids: set[str] | None = None,
    chunk_size: int = 50,
) -> list[DepartmentYearModel]:
    """Step 3: Scrapes department years for departments, validates with DepartmentYearModel, and saves to parquet."""
    if seen_class_ids is None:
        seen_class_ids = set()

    dept_models: list[DepartmentModel] = [
        d if isinstance(d, DepartmentModel) else DepartmentModel.model_validate(d)
        for d in departments_to_scrape
    ]

    all_department_years: list[DepartmentYearModel] = []
    if dept_models:
        print(
            f"Scraping department years for {len(dept_models)} departments..."
        )
        total_chunks = math.ceil(len(dept_models) / chunk_size)
        for dep_chunk in tqdm(
            batched(dept_models, chunk_size),
            total=total_chunks,
            desc="Saving department years to Parquet",
        ):
            department_years_list: list[DepartmentYearModel] = []
            raw_department_year_result = await asyncio.gather(
                *(
                    scrape(ctx=ctx, url=dept.link, tag="a")
                    for dept in dep_chunk
                )
            )

            for sublist, parent_dept in zip(raw_department_year_result, dep_chunk):
                for department_year in sublist:
                    if getattr(department_year, "name", None) == "error":
                        continue
                    href = department_year.get("href")
                    if not href:
                        continue
                    href = str(href)
                    match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", href)
                    if match:
                        year = match.group(1)
                        sem_num = match.group(2)
                        code = match.group(3).zfill(4)
                        class_id = f"{year}_{sem_num}_{parent_dept.code}_{code}"
                        if class_id not in seen_class_ids:
                            seen_class_ids.add(class_id)
                            model = DepartmentYearModel(
                                id=class_id,
                                department_id=parent_dept.id,
                                year=year,
                                sem=sem_num,
                                code=code,
                                name=department_year.text.strip(),
                                link=href,
                            )
                            department_years_list.append(model)

            if department_years_list:
                await append_to_parquet(
                    table_name="department_years", new_records=department_years_list, parquet_dir=parquet_dir
                )
                all_department_years.extend(department_years_list)

    return all_department_years
