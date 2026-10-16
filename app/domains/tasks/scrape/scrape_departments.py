import asyncio
from itertools import batched
import math
from anyio import Path
import re
from typing import Any

from tqdm.auto import tqdm

from app.domains.courses.schemas import DepartmentModel, SemesterModel
from app.domains.tasks.parquet_utils import append_to_parquet
from app.domains.tasks.scrape_utils import scrape


async def scrape_departments(
    ctx: dict[str, Any],
    parquet_dir: Path,
    sems_to_scrape: list[SemesterModel] | list[dict[str, Any]],
    seen_dep_ids: set[str] | None = None,
    chunk_size: int = 50,
) -> list[DepartmentModel]:
    """Step 2: Scrapes departments for semesters and saves/returns DepartmentModel instances."""
    if seen_dep_ids is None:
        seen_dep_ids = set()

    sem_models: list[SemesterModel] = [
        s if isinstance(s, SemesterModel) else SemesterModel.model_validate(s)
        for s in sems_to_scrape
    ]

    all_new_departments: list[DepartmentModel] = []
    if sem_models:
        print(f"Scraping departments for {len(sem_models)} semesters...")
        total_chunks = math.ceil(len(sem_models) / chunk_size)
        for sem_chunk in tqdm(
            batched(sem_models, chunk_size),
            total=total_chunks,
            desc="Saving departments to Parquet",
        ):
            new_departments: list[DepartmentModel] = []
            raw_department_result = await asyncio.gather(
                *(
                    scrape(ctx=ctx, url=sem.link, tag="a")
                    for sem in sem_chunk
                )
            )

            for sublist in raw_department_result:
                for dep in sublist:
                    match = re.search(
                        r"year=(\d+)&sem=(\d+)&code=(\d+)", str(dep.get("href", ""))
                    )
                    if match:
                        year = match.group(1)
                        sem_num = match.group(2)
                        code = match.group(3).zfill(3)
                        dep_id = f"{year}_{sem_num}_{code}"
                        if dep_id not in seen_dep_ids:
                            seen_dep_ids.add(dep_id)
                            model = DepartmentModel(
                                id=dep_id,
                                semester_id=f"{year}_{sem_num}",
                                year=year,
                                sem=sem_num,
                                code=code,
                                name=dep.text.strip(),
                                link=str(dep.get("href", "")),
                            )
                            new_departments.append(model)

            if new_departments:
                await append_to_parquet(table_name="departments", new_records=new_departments, parquet_dir=parquet_dir)
                all_new_departments.extend(new_departments)

    return all_new_departments
