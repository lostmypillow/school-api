import asyncio
import logging
import re
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.crud import (
    get_scraped_department_ids_for_classes,
    get_scraped_semester_ids_for_departments,
    save_api_payload,
)
from app.db.models import Department
from app.dependencies import get_db_session, scrape

logger = logging.getLogger("uvicorn.error")



async def sync_ntut_data(session_factory: async_sessionmaker) -> None:
    """Out-of-band task: Fetches external HTTP catalog, saves to Postgres, updates Cache."""
    start_time = time.time()
    logger.info("Starting external catalog sync via httpx...")

    try:
        async with get_db_session(factory=session_factory) as session:
            scraped_sems = await scrape(url="course.jsp", tag="sem")
            logger.info('Successfully scraped raw semesters data', extra={"Length": len(scraped_sems)})
            semester_list = []
        
            for sem in scraped_sems:
                years = re.findall(r"\d+", sem.text)
                if len(years) >= 2:
                    semester_list.append(
                        {
                            "id": f"{years[0]}_{years[1]}",
                            "year": years[0],
                            "sem": years[1],
                            "link": sem["href"],
                        }
                    )
            logger.info('Successfully processed semesters data', extra={"Length": len(semester_list)})
            # Save semesters first so foreign key constraints hold
            if semester_list:
                logger.info("Preparing to save semester data to database...")
                await save_api_payload(session, {"sem_list": semester_list})
                logger.info("Successfully saved semester data into database")
        
            # ---------------------------------------------------------
            # 2. Departments
            # ---------------------------------------------------------
            # Retrieve semester IDs that already have departments in DB
            logger.info("Preparing to retreive existing semster IDs for departments...")
            existing_sem_ids = await get_scraped_semester_ids_for_departments(session)
            logger.info("Successfully retreived existing semster IDs for departments")

            sems_to_scrape = [
                sem for sem in semester_list if sem["id"] not in existing_sem_ids
            ]
            logger.info("Semesters that do not have departments in DB yet", extra={"Length": len(sems_to_scrape)})
        
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
                        match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", str(dep["href"]))
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
                logger.info("All department links are up to date in DB. Skipping semester network calls.")


        
            logger.info("Preparing to retrieve all departments from DB...")
            all_dept_records = (await session.scalars(select(Department))).all()
        
            # ---------------------------------------------------------
            # 3. Department years (Conditional Scraping)
            # ---------------------------------------------------------
            # Retrieve department IDs that already have classes in DB
            existing_scraped_dept_ids = await get_scraped_department_ids_for_classes(session)
        
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
        
                for sublist, parent_dept in zip(raw_department_year_result, depts_to_scrape):
                    for department_year in sublist:
                        href = str(department_year["href"])
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
                    await save_api_payload(session, {"dep_year_list": department_years_list})
            else:
                print("All department classes are up to date in DB. Skipping network calls.")
        
            end_time = time.time()
        logger.info({
                "time": f"{round(end_time - start_time, 2)}s",
                "message": "Data scrape and database sync complete!",
                "new_classes_scraped": len(department_years_list),
            })


        logger.info("NTUT -> DB sync completed.")

    except Exception:
        logger.exception("NTUT -> DB sync failed")