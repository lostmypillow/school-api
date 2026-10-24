from datetime import date
from anyio import Path
import re
from typing import Any

from app.domains.courses.lib.CustomAsyncClient import client
from app.domains.courses.schemas import SemesterModel
from app.domains.courses.lib.parquet_utils import append_to_parquet



def generate_semesters() -> list[SemesterModel]:
    """Generates catalog semester records from current ROC year down to 86 as SemesterModel instances."""
    current_year = date.today().year - 1911
    current_semester = 1 if date.today().month - 6 >= 0 else 2
    current_sem_id = f"{str(current_year)}_{str(current_semester)}"

    semester_list: list[SemesterModel] = [
        SemesterModel(
            id=current_sem_id,
            year=str(current_year),
            sem=str(current_semester),
            link=f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
        )
    ]
    y = current_year
    s = current_semester
    while y >= 86:
        if s == 2:
            s = 1
        elif s == 1:
            s = 2
            y -= 1
        semester_list.append(
            SemesterModel(
                id=f"{str(y)}_{str(s)}",
                year=str(y),
                sem=str(s),
                link=f"Subj.jsp?format=-2&year={str(y)}&sem={str(s)}",
            )
        )
    return semester_list


async def scrape_semesters(url: str = "Subj.jsp?format=-1") -> list[SemesterModel]:
    """Scrapes semesters from a live NTUT root page and returns them as SemesterModel instances."""
    raw_sem_tags = await client.scrape(url=url, tag="sem")
    scraped_semesters: list[SemesterModel] = []
    for tag in raw_sem_tags:
        href = str(tag.get("href", ""))
        match = re.search(pattern=r"year=(\d+)&sem=(\d+)", string=href)
        if match:
            year = match.group(1)
            sem_num = match.group(2)
            model = SemesterModel(
                id=f"{year}_{sem_num}",
                year=year,
                sem=sem_num,
                name=tag.text.strip(),
                link=href,
            )
            scraped_semesters.append(model)
    return scraped_semesters


async def sync_semesters(
    parquet_dir: Path,
    semester_list: list[SemesterModel] | list[dict[str, Any]] | None = None,
) -> list[SemesterModel]:
    """Step 1: Save semesters directly to semesters.parquet as SemesterModel instances."""
    if semester_list is None:
        models = generate_semesters()
    else:
        models = [
            s if isinstance(s, SemesterModel) else SemesterModel.model_validate(s)
            for s in semester_list
        ]
    await append_to_parquet(table_name="semesters", new_records=models, parquet_dir=parquet_dir)
    return models
