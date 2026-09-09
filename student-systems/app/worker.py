# worker.py
from datetime import date
from pathlib import Path
from arq.connections import RedisSettings

import os
import asyncio
import logging
import re
import time

from sqlalchemy import select

from app.db.crud import (
    get_scraped_department_ids_for_classes,
    get_scraped_semester_ids_for_departments,
    save_api_payload,
)
from app.db.models import Department
from app.dependencies import get_db_session, scrape, create_db_factory

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

async def startup(ctx: dict):
    db_url = os.getenv("DB_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}")
    if not db_url:
        raise ValueError(
            "DB_URL environment variable is not set for the ARQ worker process."
        )

    engine, session_factory = create_db_factory(db_url=db_url)

    # Store in worker context
    ctx["engine"] = engine
    ctx["session_factory"] = session_factory
    print("ARQ Worker initialized database engine and session factory.")


async def shutdown(ctx: dict):
    engine = ctx.get("engine")
    if engine:
        await engine.dispose()
        print("ARQ Worker database engine disposed.")

async def sync_ntut_data(ctx:dict) -> None:
    """Out-of-band task: Fetches external HTTP catalog, saves to Postgres, updates Cache."""
    start_time = time.time()
    session_factory = ctx["session_factory"]
    print("Starting external catalog sync via httpx...")

    try:
        async with get_db_session(factory=session_factory) as session:
            semester_list = []
            current_year = date.today().year-1911
            current_semester = 2 if date.today().month -6 >= 0 else 1
            semester_list.append(
                {
                    "id": f"{str(current_year)}_{str(current_semester)}",
                    "year": str(current_year),
                    "sem": str(current_semester),
                    "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}"
                })
            while True:
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
                    if current_year == 86 and current_semester == 1:
                        break
            print(
                f"Successfully processed semesters data. Length: {len(semester_list)}"
            )
            # Save semesters first so foreign key constraints hold
            if semester_list:
                print("Preparing to save semester data to database...")
                await save_api_payload(session, {"sem_list": semester_list})
                print("Successfully saved semester data into database")

            # ---------------------------------------------------------
            # 2. Departments
            # ---------------------------------------------------------
            # Retrieve semester IDs that already have departments in DB
            print("Preparing to retreive existing semster IDs for departments...")
            existing_sem_ids = await get_scraped_semester_ids_for_departments(session)
            print("Successfully retreived existing semster IDs for departments")

            sems_to_scrape = [
                sem for sem in semester_list if sem["id"] not in existing_sem_ids
            ]
            print(
                f"Semesters that do not have departments in DB yet. Length {len(sems_to_scrape)}",
            )

            new_departments = []
            seen_dep_ids = set()
            if sems_to_scrape:
                print(
                    f"Scraping departments for {len(sems_to_scrape)} new/missing semesters (Skipped {len(semester_list) - len(sems_to_scrape)} existing)..."
                )
                raw_department_result = await asyncio.gather(
                    *(scrape(url=sem["link"], tag="a") for sem in sems_to_scrape)
                )

                for sublist in raw_department_result:
                    for dep in sublist:
                        match = re.search(
                            r"year=(\d+)&sem=(\d+)&code=(\d+)", str(dep["href"])
                        )
                        if match:
                            year = match.group(1)
                            sem = match.group(2)
                            code = match.group(3)
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
                    await save_api_payload(session, {"dep_list": new_departments})
            else:
                print(
                    "All department links are up to date in DB. Skipping semester network calls."
                )

            print("Preparing to retrieve all departments from DB...")
            all_dept_records = (await session.scalars(select(Department))).all()

            # ---------------------------------------------------------
            # 3. Department years (Conditional Scraping)
            # ---------------------------------------------------------
            # Retrieve department IDs that already have classes in DB
            existing_scraped_dept_ids = await get_scraped_department_ids_for_classes(
                session
            )

            # FILTER: Only make HTTP requests for departments whose classes aren't in DB yet
            depts_to_scrape = [
                dept
                for dept in all_dept_records
                if dept.id not in existing_scraped_dept_ids and dept.link
            ]

            department_years_list = []
            seen_class_ids = set()
            if depts_to_scrape:
                print(
                    f"Scraping {len(depts_to_scrape)} new/missing department classes (Skipped {len(all_dept_records) - len(depts_to_scrape)} existing)..."
                )

                raw_department_year_result = await asyncio.gather(
                    *(scrape(str(dept.link), tag="a") for dept in depts_to_scrape)
                )

                for sublist, parent_dept in zip(
                    raw_department_year_result, depts_to_scrape
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
                            code = match.group(3)
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

                # Upsert newly fetched classes
                if department_years_list:
                    await save_api_payload(
                        session, {"dep_year_list": department_years_list}
                    )
            else:
                print(
                    "All department classes are up to date in DB. Skipping network calls."
                )

            end_time = time.time()
        print(
            {
                "time": f"{round(end_time - start_time, 2)}s",
                "message": "Data scrape and database sync complete!",
                "new_classes_scraped": len(department_years_list),
            }
        )

        print("NTUT -> DB sync completed.")

    except Exception:
        logger.exception("NTUT -> DB sync failed")

# 2. Configure the ARQ Worker Class
class WorkerSettings:
    functions = [sync_ntut_data]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    max_jobs = 10  # Limit concurrent scraping jobs
    job_timeout = 300  # 5-minute timeout per scrape
    on_startup = startup
    on_shutdown = shutdown
