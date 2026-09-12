import asyncio
import re
import time
from datetime import date
from itertools import batched
import logging
import math
from tqdm.auto import tqdm

from bs4 import BeautifulSoup
from sqlalchemy import select
from tqdm.asyncio import tqdm_asyncio

from app.db.crud import save_ntut_operations
from app.db.initialize import DB
from app.db.models import Department, DepartmentYear
from app.workers.http_client import scrape
from app.db.models import Semester

logger = logging.getLogger(__name__)
async def bootstrap_sqlite(ctx: dict) -> None:
    """Out-of-band task: Fetches external HTTP catalog, saves to Postgres, updates Cache."""
    start_time = time.time()
    db: DB = ctx["db"]
    print("Starting external catalog sync via httpx...")

    try:
        async with db.get_session() as session:
            semester_list = []
            current_year = date.today().year - 1911
            current_semester = 2 if date.today().month - 6 >= 0 else 1
            semester_list.append(
                {
                    "id": f"{str(current_year)}_{str(current_semester)}",
                    "year": str(current_year),
                    "sem": str(current_semester),
                    "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
                }
            )
            while current_year < 86:
                if current_semester == 2:
                    current_semester = 1
                elif current_semester == 1:
                    current_semester = 2
                    current_year -= 1
                semester_list.append(
                    {
                        "id": f"{str(current_year)}_{str(current_semester)}",
                        "year": str(current_year),
                        "sem": str(current_semester),
                        "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
                    }
                )
            print(
                f"Successfully processed semesters data. Length: {len(semester_list)}"
            )
            # Save semesters first so foreign key constraints hold
            if semester_list:
                print("Preparing to save semester data to database...")
                await save_ntut_operations(session, {"sem_list": semester_list})
                print("Successfully saved semester data into database")

            # ---------------------------------------------------------
            # 2. Departments
            # ---------------------------------------------------------
            # Retrieve semester IDs that already have departments in DB
            print("Preparing to retrieve existing semster IDs for departments...")
            results = await session.scalars(select(Semester).distinct())


            sems_to_scrape = {r for r in results.all() if r is not None}

            new_departments = []
            seen_dep_ids = set()
            if sems_to_scrape:
                print(
                    f"Scraping departments for {len(sems_to_scrape)} semesters..."
                )
                raw_department_result = await tqdm_asyncio.gather(
                    *(scrape(ctx=ctx, url=str(sem.link), tag="a") for sem in sems_to_scrape)
                )

                for sublist in raw_department_result:
                    for dep in sublist:
                        match = re.search(
                            r"year=(\d+)&sem=(\d+)&code=(\d+)", str(dep["href"])
                        )
                        if match:
                            year = match.group(1)
                            sem = match.group(2)
                            code = match.group(3).zfill(3)
                            dep_id = f"{year}_{sem}_{code}"
                            if dep_id not in seen_dep_ids:
                                seen_dep_ids.add(dep_id)
                                new_departments.append(
                                    {
                                        "id": dep_id,
                                        "semester_id": f"{year}_{sem}",
                                        "year": year,
                                        "sem": sem,
                                        "code": code,
                                        "name": dep.text,
                                        "link": dep["href"],
                                    }
                                )

            if new_departments:
                await save_ntut_operations(session, {"dep_list": new_departments})
                print("Successfully saved department data into database")




            all_dept_records = (await session.scalars(select(Department))).all()

            department_years_list = []
            seen_class_ids = set()
            if all_dept_records:
                print(
                    f"Scraping department years for {len(all_dept_records)}  departments..."
                )

                raw_department_year_result = await tqdm_asyncio.gather(
                    *(scrape(ctx=ctx, url=str(dept.link), tag="a") for dept in all_dept_records)
                )
       
                for sublist, parent_dept in zip(
                    raw_department_year_result, all_dept_records
                ):
                    for department_year in sublist:
                        if department_year.name == "error":
                            continue
                        href = department_year.get("href")
                        if not href:
                            continue
                        href = str(href)
                        match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", href)
                        if match:
                            year = match.group(1)
                            sem = match.group(2)
                            code = match.group(3).zfill(4)
                            class_id = f"{year}_{sem}_{parent_dept.code}_{code}"
                            if class_id not in seen_class_ids:
                                seen_class_ids.add(class_id)
                                department_years_list.append(
                                    {
                                        "id": class_id,
                                        "department_id": parent_dept.id,
                                        "year": year,
                                        "sem": sem,
                                        "code": code,
                                        "name": department_year.text,
                                        "link": department_year["href"],
                                    }
                                )
                
            if department_years_list:
                batch_size = 50
                total_batches = math.ceil(len(department_years_list) / batch_size)
                for batch in tqdm(
                            batched(department_years_list, batch_size),
                            total=total_batches,
                            desc="Saving department years to DB"
                    ):
                        batch_list = list(batch)
                        await save_ntut_operations(session, {"dep_year_list": batch_list})


            print("Successfully saved department years data into database")


            #           Courses
            
            all_dep_year_records = (await session.scalars(select(DepartmentYear))).all()
            print(f"all_dep_year_records: {len(all_dep_year_records)}")




            dep_years_to_scrape = all_dep_year_records
            CHUNK_SIZE = 50


            if dep_years_to_scrape:
                print(
                    f"Scraping courses for {len(dep_years_to_scrape)} department years (Skipped {len(all_dep_year_records) - len(dep_years_to_scrape)} existing)..."
                )
                total_chunks = math.ceil(len(dep_years_to_scrape) / CHUNK_SIZE)
                for dep_year_chunk in tqdm(
                        batched(dep_years_to_scrape, CHUNK_SIZE),
                        total=total_chunks,
                        desc="Scraping & Saving Courses",
                        mininterval=5.0,
                        ascii=True
                ):
                    course_list = []
                    
                    raw_course_result = await asyncio.gather(
                        *(
                            scrape(ctx=ctx,url=str(dep_year.link), tag="tr")
                            for dep_year in dep_year_chunk
                        )
                    )


                    for sublist, parent_dep_year in zip(
                        raw_course_result, dep_year_chunk
                    ):
                        for course in sublist:
                            soup = BeautifulSoup(str(course), "lxml")
                            cells = soup.find_all("td")
                            if len(cells) == 0:
                                soup.decompose()
                                continue
                            try:
                                a_tag = cells[18].find("a")
                                course_list.append(
                                    {
                                        "id": f"{parent_dep_year.year}_{parent_dep_year.sem}_{parent_dep_year.code}_{cells[0].text.strip() if cells[0].text.strip() else 'nocode'}",
                                        "department_year_id": parent_dep_year.id,
                                        "year":parent_dep_year.year,
                                        "sem": parent_dep_year.sem,
                                        "code": cells[0].text.strip().zfill(6)
                                        if cells[0].text.strip()
                                        else None,
                                        "name": cells[1].text.strip()
                                        if cells[1].text.strip()
                                        else None,
                                        "credits": (cells[2].text.strip())
                                        if cells[2].text.strip()
                                        else None,
                                        "course_type": cells[5].text.strip()
                                        if cells[5].text.strip()
                                        else None,
                                        "instructor": cells[6].text.strip()
                                        if cells[6].text.strip()
                                        else None,
                                        "sun": cells[7].text.strip()
                                        if cells[7].text.strip()
                                        else None,
                                        "mon": cells[8].text.strip()
                                        if cells[8].text.strip()
                                        else None,
                                        "tue": cells[9].text.strip()
                                        if cells[9].text.strip()
                                        else None,
                                        "wed": cells[10].text.strip()
                                        if cells[10].text.strip()
                                        else None,
                                        "thu": cells[11].text.strip()
                                        if cells[11].text.strip()
                                        else None,
                                        "fri": cells[12].text.strip()
                                        if cells[12].text.strip()
                                        else None,
                                        "sat": cells[13].text.strip()
                                        if cells[13].text.strip()
                                        else None,
                                        "classroom": cells[14].text.strip()
                                        if cells[14].text.strip()
                                        else None,
                                        "students_enrolled": int(cells[15].text.strip())
                                        if cells[15].text.strip()
                                        else None,
                                        "students_dropped": int(cells[16].text.strip())
                                        if cells[16].text.strip()
                                        else None,
                                        "language": cells[17].text.strip()
                                        if cells[17].text.strip()
                                        else None,
                                        "link": str(a_tag["href"])
                                        if a_tag and "href" in a_tag.attrs
                                        else None,
                                        "notes": cells[19].text.strip()
                                        if cells[19].text.strip()
                                        else None,
                                        "with_class": cells[20].text.strip()
                                        if cells[20].text.strip()
                                        else None,
                                        "experiment": cells[21].text.strip()
                                        if cells[21].text.strip()
                                        else None,
                                        "cross_discipline": cells[22].text.strip()
                                        if cells[22].text.strip()
                                        else None,
                                    }
                                )
                            except IndexError:
                                continue
                            finally:
                                soup.decompose()

                if course_list:
                    await save_ntut_operations(session, {"course_list": course_list})
            print("Successfully saved courses data into database")

            end_time = time.time()
        print(
            {
                "time": f"{round(end_time - start_time, 2)}s",
                "message": "Data scrape and database sync complete!",
            }
        )

        print("NTUT -> DB sync completed.")

    except Exception:
        logger.exception("NTUT -> DB sync failed")


