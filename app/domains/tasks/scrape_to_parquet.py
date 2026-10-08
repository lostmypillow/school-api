import asyncio
import hashlib
import inspect
import logging
import math

from datetime import date
from itertools import batched
from pathlib import Path
import re
import time
import traceback
from typing import Any
import uuid

from bs4 import BeautifulSoup
import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm.auto import tqdm

from app.core.custom_http_client import CustomAsyncClient

logger = logging.getLogger(__name__)


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    try:
        s = str(val).strip()
        return int(float(s)) if s else None
    except (ValueError, TypeError):
        return None


def _read_parquet_records(file_path: Path) -> list[dict[str, Any]]:
    """Reads a Parquet file and returns a list of row dictionaries."""
    if not file_path.exists():
        return []
    return pq.read_table(file_path).to_pylist()


def _append_to_parquet(
    table_name: str,
    new_records: list[dict[str, Any]],
    parquet_dir: Path,
    compression: str = "snappy",
) -> Path:
    """Appends records to a Parquet file, deduplicating by primary key 'id'."""
    file_path = parquet_dir / f"{table_name}.parquet"
    existing_records = _read_parquet_records(file_path)
    seen_ids = {r["id"] for r in existing_records if "id" in r}

    combined = list(existing_records)
    for r in new_records:
        r_id = r.get("id")
        if r_id is None or r_id not in seen_ids:
            row_copy = dict(r)
            for k, v in row_copy.items():
                if hasattr(v, "isoformat"):
                    row_copy[k] = v.isoformat()
            combined.append(row_copy)
            if r_id is not None:
                seen_ids.add(r_id)

    if combined:
        arrow_table = pa.Table.from_pylist(combined)
    else:
        arrow_table = pa.Table.from_pydict({})

    pq.write_table(arrow_table, file_path, compression=compression)
    return file_path


async def scrape_to_parquet(ctx: dict | None = None, *args, **kwargs) -> None:
    """Scrapes NTUT catalog and writes directly to Parquet snapshot files."""
    start_time = time.time()
    if ctx is None:
        ctx = {}
    if "parquet_dir" not in ctx:
        DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
        parquet_dir = DATA_DIR / "parquet"
        parquet_dir.mkdir(parents=True, exist_ok=True)
        ctx["parquet_dir"] = parquet_dir
    else:
        parquet_dir = Path(ctx["parquet_dir"])
        parquet_dir.mkdir(parents=True, exist_ok=True)
    if "client" not in ctx:
        ctx["client"] = CustomAsyncClient(
            verify=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
            timeout=30.0,
        )

    print(f"Starting catalog scrape (writing directly to Parquet at {parquet_dir})...")

    try:
        dept_records = _read_parquet_records(parquet_dir / "departments.parquet")
        dy_records = _read_parquet_records(parquet_dir / "department_years.parquet")
        course_records = _read_parquet_records(parquet_dir / "courses.parquet")

        existing_dept_semester_ids = {
            r["semester_id"] for r in dept_records if "semester_id" in r
        }
        department_with_years = {
            r["department_id"] for r in dy_records if "department_id" in r
        }
        department_years_with_courses = {
            r["department_year_id"] for r in course_records if "department_year_id" in r
        }

        seen_dep_ids: set[str] = set()
        seen_class_ids: set[str] = set()

        CHUNK_SIZE = 50
        current_year = date.today().year - 1911
        current_semester = 1 if date.today().month - 6 >= 0 else 2
        current_sem_id = f"{str(current_year)}_{str(current_semester)}"

        # ---------------------------------------------------------
        # 1. Semesters -> Save directly to semesters.parquet
        # ---------------------------------------------------------
        semester_list = [
            {
                "id": current_sem_id,
                "year": str(current_year),
                "sem": str(current_semester),
                "link": f"Subj.jsp?format=-2&year={str(current_year)}&sem={str(current_semester)}",
            }
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
                {
                    "id": f"{str(y)}_{str(s)}",
                    "year": str(y),
                    "sem": str(s),
                    "link": f"Subj.jsp?format=-2&year={str(y)}&sem={str(s)}",
                }
            )

        _append_to_parquet("semesters", semester_list, parquet_dir)

        # ---------------------------------------------------------
        # 2. Departments -> Skip semesters already in Parquet
        # ---------------------------------------------------------
        sems_to_scrape = [
            sem
            for sem in semester_list
            if sem["id"] not in existing_dept_semester_ids
            or sem["id"] == current_sem_id
        ]

        if sems_to_scrape:
            print(f"Scraping departments for {len(sems_to_scrape)} semesters...")
            total_chunks = math.ceil(len(sems_to_scrape) / CHUNK_SIZE)
            for sem_chunk in tqdm(
                batched(sems_to_scrape, CHUNK_SIZE),
                total=total_chunks,
                desc="Saving departments to Parquet",
            ):
                new_departments = []
                raw_department_result = await asyncio.gather(
                    *(
                        scrape(ctx=ctx, url=str(sem["link"]), tag="a")
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
                                new_departments.append(
                                    {
                                        "id": dep_id,
                                        "semester_id": f"{year}_{sem_num}",
                                        "year": year,
                                        "sem": sem_num,
                                        "code": code,
                                        "name": dep.text,
                                        "link": dep.get("href", ""),
                                    }
                                )

                if new_departments:
                    _append_to_parquet("departments", new_departments, parquet_dir)

        # ---------------------------------------------------------
        # 3. Department Years -> Skip departments already in Parquet
        # ---------------------------------------------------------
        all_departments = _read_parquet_records(parquet_dir / "departments.parquet")

        depts_to_scrape = [
            d
            for d in all_departments
            if d.get("id") not in department_with_years
            or d.get("semester_id") == current_sem_id
        ]

        if depts_to_scrape:
            print(
                f"Scraping department years for {len(depts_to_scrape)} departments..."
            )
            total_chunks = math.ceil(len(depts_to_scrape) / CHUNK_SIZE)
            for dep_chunk in tqdm(
                batched(depts_to_scrape, CHUNK_SIZE),
                total=total_chunks,
                desc="Saving department years to Parquet",
            ):
                department_years_list = []
                raw_department_year_result = await asyncio.gather(
                    *(
                        scrape(ctx=ctx, url=str(dept.get("link", "")), tag="a")
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
                            class_id = f"{year}_{sem_num}_{parent_dept['code']}_{code}"
                            if class_id not in seen_class_ids:
                                seen_class_ids.add(class_id)
                                department_years_list.append(
                                    {
                                        "id": class_id,
                                        "department_id": parent_dept["id"],
                                        "year": year,
                                        "sem": sem_num,
                                        "code": code,
                                        "name": department_year.text,
                                        "link": href,
                                    }
                                )

                if department_years_list:
                    _append_to_parquet(
                        "department_years", department_years_list, parquet_dir
                    )

        # ---------------------------------------------------------
        # 4. Courses -> Skip department years already in Parquet
        # ---------------------------------------------------------
        all_dep_years = _read_parquet_records(
            parquet_dir / "department_years.parquet"
        )

        dep_years_to_scrape = [
            dy
            for dy in all_dep_years
            if dy.get("id") not in department_years_with_courses
            or str(dy.get("id", "")).startswith(current_sem_id)
        ]

        if dep_years_to_scrape:
            print(
                f"Scraping courses for {len(dep_years_to_scrape)} department years..."
            )
            total_chunks = math.ceil(len(dep_years_to_scrape) / CHUNK_SIZE)
            for dep_year_chunk in tqdm(
                batched(dep_years_to_scrape, CHUNK_SIZE),
                total=total_chunks,
                desc="Saving Courses to Parquet",
            ):
                course_list = []
                raw_course_result = await asyncio.gather(
                    *(
                        scrape(ctx=ctx, url=str(dep_year.get("link", "")), tag="tr")
                        for dep_year in dep_year_chunk
                    )
                )

                for sublist, parent_dep_year in zip(raw_course_result, dep_year_chunk):
                    for course in sublist:
                        soup = BeautifulSoup(str(course), "lxml")
                        cells = soup.find_all("td")
                        if len(cells) == 0:
                            soup.decompose()
                            continue
                        try:
                            a_tag = cells[18].find("a")
                            code_text = (
                                cells[0].text.strip()
                                if cells[0].text.strip()
                                else cells[1].text.strip()
                            )
                            course_id = f"{parent_dep_year['year']}_{parent_dep_year['sem']}_{parent_dep_year['code']}_{code_text}"

                            course_list.append(
                                {
                                    "id": course_id,
                                    "department_year_id": parent_dep_year["id"],
                                    "year": parent_dep_year["year"],
                                    "sem": parent_dep_year["sem"],
                                    "code": cells[0].text.strip().zfill(6)
                                    if cells[0].text.strip()
                                    else None,
                                    "name": cells[1].text.strip()
                                    if cells[1].text.strip()
                                    else None,
                                    "credits": _safe_int(cells[2].text.strip()),
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
                                    "students_enrolled": _safe_int(
                                        cells[15].text.strip()
                                    ),
                                    "students_dropped": _safe_int(
                                        cells[16].text.strip()
                                    ),
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
                    _append_to_parquet("courses", course_list, parquet_dir)

        end_time = time.time()
        print(
            {
                "time": f"{round(end_time - start_time, 2)}s",
                "message": "Data scrape and Parquet sync complete!",
            }
        )
        print("NTUT -> Parquet sync completed.")

    except Exception:
        logger.exception("NTUT -> Parquet sync failed")
        raise
    finally:
        client = ctx.get("client")
        if client is not None and hasattr(client, "aclose") and not client.is_closed:
            await client.aclose()


async def scrape(ctx: dict, url: str, tag: str):
    """Scrapes using the shared internal HTTP client with error handling and Redis caching."""
    redis = ctx.get("redis")
    client: CustomAsyncClient = ctx["client"]

    async with client.semaphore:
        combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
        bs4_mode = "html.parser" if tag == "sem" else "lxml"

        if tag == "sem":

            def bs4_function(t):
                return t.name == "a" and t.get("href", "").startswith("Subj")
        else:
            bs4_function = tag

        try:
            html_text = await fetch_html(ctx, redis, combined_url)
            return BeautifulSoup(html_text, bs4_mode).find_all(bs4_function)

        except httpx.HTTPError as exc:
            error_id = str(uuid.uuid4())
            req_info = (
                f"{exc.request.method} {exc.request.url}"
                if exc.request
                else "No request"
            )
            resp_info = ""
            if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                resp_info = f" | Status: {exc.response.status_code} | Body: {exc.response.text[:300]}"
            print(
                f"[ERROR ID {error_id}] [{type(exc).__name__}] {req_info}{resp_info} => {exc}"
            )
            print(traceback.format_exc())
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")

        except Exception as e:
            error_id = str(uuid.uuid4())
            print(f"[ERROR ID {error_id}] [{type(e).__name__}] => {e}")
            print(traceback.format_exc())
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")


async def fetch_html(
    ctx: dict,
    redis: Any | None,
    combined_url: str,
    ttl_seconds: int = 86400,
    max_retries: int = 3,
) -> str:
    """Fetches raw HTML from Redis cache if available, or falls back to HTTP request with retries."""
    if redis is not None:
        url_hash = hashlib.sha256(combined_url.encode("utf-8")).hexdigest()
        cache_key = f"cache:html:{url_hash}"

        cached_val = redis.get(cache_key)
        if inspect.isawaitable(cached_val):
            cached_val = await cached_val

        if cached_val is not None:
            if isinstance(cached_val, bytes):
                return cached_val.decode("utf-8")
            return cached_val

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = await ctx["client"].get(combined_url)
            response.raise_for_status()
            html_text = response.text
            break
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (2**attempt))
            else:
                raise last_exc

    if redis is not None:
        set_result = redis.set(cache_key, html_text, ex=ttl_seconds)
        if inspect.isawaitable(set_result):
            await set_result
    return html_text


