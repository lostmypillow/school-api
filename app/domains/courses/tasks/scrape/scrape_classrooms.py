import asyncio
import gc
from itertools import batched
import math
from os import name

from anyio import Path
from typing import Any

from bs4 import BeautifulSoup, Tag
from tqdm.auto import tqdm

from app.domains.courses.lib.CustomAsyncClient import client, CustomAsyncClient
from app.domains.courses.schemas import CourseModel, CourseSyllabusModel
from app.domains.courses.lib.parquet_utils import (
    consolidate_parquet_chunks,
    write_parquet_chunk,
)



async def parse_course_syllabus(
    tr_elements: list[Tag] | list[Any],
    course: CourseModel,
    schedule_map: dict[str, str] | None = None,
):

    instructor_schedule = ""

    for course_tag in tr_elements:
        tag = (
            course_tag
            if isinstance(course_tag, Tag)
            else BeautifulSoup(markup=str(course_tag), features="html.parser")
        )
        try:
            scrape_key = tag.find(name="th")
            key = scrape_key.get_text(strip=True).strip() if scrape_key else ""
            scrape_value = tag.find(name="td")
            if not scrape_value:
                scrape_value = tag.find(name="th", align="left")
                a_tag = tag.find("a")
                href = a_tag.get("href") if a_tag else ""
                href_str = str(href) if href else ""
                if href_str and not href_str.startswith("mailto"):
                    if schedule_map is not None and href_str in schedule_map:
                        instructor_schedule = schedule_map[href_str]
                    elif schedule_map is None:
                        res = await client.scrape(url=href_str, tag="body")
                        res_list = str(res).strip().split("<br/>")
                        for r in res_list:
                            r_str = r.strip()
                            if r_str.startswith("星期"):
                                instructor_schedule += f"\n{r_str.replace('\u3000', ' ')}"
                        instructor_schedule = instructor_schedule.strip()

            value = (
                scrape_value.get_text(separator="\n", strip=True).strip()
                if scrape_value
                else ""
            )
            value = value.split("教師諮商時間")[0].strip()
            if key != "" and value != "":
                parsed_result[key] = value.strip()
        except IndexError:
            pass

    if instructor_schedule != "":
        parsed_result["instructor_schedule"] = instructor_schedule

    if not parsed_result:
        return None

    renamed_data = {
        conversion_dict.get(k, k): v.strip() for k, v in parsed_result.items()
    }

    syllabus_id = f"{course.id}_syllabus"

    return CourseSyllabusModel(
        id=syllabus_id,
        course_id=course.id,
        **renamed_data,
    )


parse_courses_syllabi_row = parse_course_syllabus


async def scrape_courses_syllabi(
    parquet_dir: Path,
    course_to_scrape: list[CourseModel] | list[dict[str, Any]],
    chunk_size: int = 50,
):
    res =  client.scrape(
        url="https://aps.ntut.edu.tw/course/tw/Croom.jsp?format=-2&year=115&sem=1", tag="tr")
    print(res)
    # course_models: list[CourseModel] = [
    #     dy if isinstance(dy, CourseModel) else CourseModel.model_validate(dy)
    #     for dy in course_to_scrape
    # ]
    #
    # if course_models:
    #     print(f"Scraping syllabi for {len(course_models)} courses...")
    #     total_chunks = math.ceil(len(course_models) / chunk_size)
    #     for chunk_idx, course_chunk in enumerate(
    #         tqdm(
    #             batched(course_models, chunk_size),
    #             total=total_chunks,
    #             desc="Saving Courses Syllabi to Parquet",
    #         )
    #     ):
    #         course_syllabi_list: list[CourseSyllabusModel] = []
    #         chunk: list[CourseModel] = [c for c in course_chunk if c.link]
    #
    #         raw_course_syllabi_result = await asyncio.gather(
    #             *(
    #                 client.scrape(url=course.link, tag="tr")
            #         for course in chunk
            #         if course.link
            #     )
            # )
            #
            # # 1. Concurrently extract and batch fetch instructor schedules across the entire chunk
            # schedule_urls: set[str] = set()
    #         for sublist in raw_course_syllabi_result:
    #             for tr in sublist:
    #                 if isinstance(tr, Tag) and not tr.find(name="td"):
    #                     th_left = tr.find(name="th", align="left")
    #                     if th_left:
    #                         a_tag = th_left.find("a")
    #                         href = a_tag.get("href") if a_tag else ""
    #                         if href and not str(href).startswith("mailto"):
    #                             schedule_urls.add(str(href))
    #
    #         schedule_map: dict[str, str] = {}
    #         if schedule_urls:
    #             url_list = list(schedule_urls)
    #             schedule_responses = await asyncio.gather(
    #                 *(client.scrape(url=u, tag="body") for u in url_list),
    #                 return_exceptions=True,
    #             )
    #             for u, res in zip(url_list, schedule_responses):
    #                 if isinstance(res, list) and res:
    #                     sched_lines = []
    #                     res_list = str(res).strip().split("<br/>")
    #                     for r in res_list:
    #                         r_str = r.strip()
    #                         if r_str.startswith("星期"):
    #                             sched_lines.append(r_str.replace("\u3000", " "))
    #                     schedule_map[u] = "\n".join(sched_lines)
    #
    #         # 2. Parse course syllabi using direct Tag navigation and the pre-fetched schedule map
    #         for sublist, parent_course in zip(raw_course_syllabi_result, chunk):
    #             parsed = await parse_course_syllabus(
    #                 tr_elements=sublist,
    #                 course=parent_course,
    #                 schedule_map=schedule_map,
    #             )
    #             if parsed is not None:
    #                 course_syllabi_list.append(parsed)
    #
    #             # Decompose tags to break circular references
    #             for t in sublist:
    #                 if isinstance(t, Tag):
    #                     t.decompose()
    #
    #         # 3. Stream chunk directly to parquet part file without reading existing records
    #         if course_syllabi_list:
    #             await write_parquet_chunk(
    #                 table_name="courses_syllabi",
    #                 new_records=course_syllabi_list,
    #                 parquet_dir=parquet_dir,
    #                 chunk_id=chunk_idx,
    #             )
    #
    #         # 4. Drop in-memory batch references and periodically trigger garbage collection
    #         del course_syllabi_list
    #         del raw_course_syllabi_result
    #         del schedule_map
    #         if chunk_idx % 10 == 0:
    #             gc.collect()
    #
    #     # 5. Consolidate all parts into final parquet file once at the end
    #     await consolidate_parquet_chunks(table_name="courses_syllabi", parquet_dir=parquet_dir)
    #     gc.collect()
    #
    # return []

