import asyncio
import gc
from itertools import batched
import math
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from tqdm.auto import tqdm

from app.domains.courses.schemas import CourseModel, DepartmentYearModel
from app.domains.tasks.parquet_utils import (
    _safe_int,
    consolidate_parquet_chunks,
    write_parquet_chunk,
)
from app.domains.tasks.scrape_utils import scrape


def parse_course_row(
    course_tag: Any,
    parent_dep_year: DepartmentYearModel | dict[str, Any],
) -> CourseModel | None:
    """Parses a single course <tr> element and returns a CourseModel instance."""
    soup = BeautifulSoup(str(course_tag), features="lxml")
    cells = soup.find_all("td")
    if len(cells) == 0:
        soup.decompose()
        return None
    try:
        parent = (
            parent_dep_year
            if isinstance(parent_dep_year, DepartmentYearModel)
            else DepartmentYearModel.model_validate(parent_dep_year)
        )
        a_tag = cells[18].find("a")
        code_text = (
            cells[0].text.strip()
            if cells[0].text.strip()
            else cells[1].text.strip()
        )
        course_id = f"{parent.year}_{parent.sem}_{parent.code}_{code_text}"

        return CourseModel(
            id=course_id,
            department_year_id=parent.id,
            year=parent.year,
            sem=parent.sem,
            code=cells[0].text.strip().zfill(6)
            if cells[0].text.strip()
            else None,
            name=cells[1].text.strip()
            if cells[1].text.strip()
            else None,
            credits=_safe_int(cells[2].text.strip()),
            course_type=cells[5].text.strip()
            if cells[5].text.strip()
            else None,
            instructor=cells[6].text.strip()
            if cells[6].text.strip()
            else None,
            sun=cells[7].text.strip()
            if cells[7].text.strip()
            else None,
            mon=cells[8].text.strip()
            if cells[8].text.strip()
            else None,
            tue=cells[9].text.strip()
            if cells[9].text.strip()
            else None,
            wed=cells[10].text.strip()
            if cells[10].text.strip()
            else None,
            thu=cells[11].text.strip()
            if cells[11].text.strip()
            else None,
            fri=cells[12].text.strip()
            if cells[12].text.strip()
            else None,
            sat=cells[13].text.strip()
            if cells[13].text.strip()
            else None,
            classroom=cells[14].text.strip()
            if cells[14].text.strip()
            else None,
            students_enrolled=_safe_int(
                cells[15].text.strip()
            ),
            students_dropped=_safe_int(
                cells[16].text.strip()
            ),
            language=cells[17].text.strip()
            if cells[17].text.strip()
            else None,
            link=str(a_tag["href"])
            if a_tag and "href" in a_tag.attrs
            else None,
            notes=cells[19].text.strip()
            if cells[19].text.strip()
            else None,
            with_class=cells[20].text.strip()
            if cells[20].text.strip()
            else None,
            experiment=cells[21].text.strip()
            if cells[21].text.strip()
            else None,
            cross_discipline=cells[22].text.strip()
            if cells[22].text.strip()
            else None,
        )
    except IndexError:
        return None
    finally:
        soup.decompose()



async def scrape_courses(
    ctx: dict[str, Any],
    parquet_dir: Path,
    dep_years_to_scrape: list[DepartmentYearModel] | list[dict[str, Any]],
    chunk_size: int = 50,
) -> list[CourseModel]:
    """Step 4: Scrapes courses for department years, validates via CourseModel, and saves to courses.parquet."""
    dy_models: list[DepartmentYearModel] = [
        dy if isinstance(dy, DepartmentYearModel) else DepartmentYearModel.model_validate(dy)
        for dy in dep_years_to_scrape
    ]

    all_courses: list[CourseModel] = []
    if dy_models:
        print(
            f"Scraping courses for {len(dy_models)} department years..."
        )
        total_chunks = math.ceil(len(dy_models) / chunk_size)
        for chunk_idx, dep_year_chunk in enumerate(
            tqdm(
                batched(dy_models, chunk_size),
                total=total_chunks,
                desc="Saving Courses to Parquet",
            )
        ):
            course_list: list[CourseModel] = []
            raw_course_result = await asyncio.gather(
                *(
                    scrape(ctx=ctx, url=dep_year.link, tag="tr")
                    for dep_year in dep_year_chunk
                )
            )

            for sublist, parent_dep_year in zip(raw_course_result, dep_year_chunk):
                for course in sublist:
                    parsed = parse_course_row(course, parent_dep_year)
                    if parsed is not None:
                        course_list.append(parsed)

            if course_list:
                write_parquet_chunk(table_name="courses", new_records=course_list, parquet_dir=parquet_dir, chunk_id=chunk_idx)
                all_courses.extend(course_list)

            del raw_course_result
            if chunk_idx % 20 == 0:
                gc.collect()

        await consolidate_parquet_chunks(table_name="courses", parquet_dir=parquet_dir)
        gc.collect()

    return all_courses
