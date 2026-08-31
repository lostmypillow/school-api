import re
import time

from app.ntut.dependencies import scrape


async def extract_years(client, year, sem, code):
    start_time = time.time()
    year_list = []
    for scraped_year in await scrape(
        client,
        "Subj.jsp?format=-3&year="
        + str(year)
        + "&sem="
        + str(sem)
        + "&code="
        + str(code),
        "a",
    ):
        href = str(scraped_year["href"])
        match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", href)
        if match:
            year_match = match.group(1)
            sem_match = match.group(2)
            code_match = match.group(3)
            year_list.append(
                {
                    "year": year_match,
                    "sem": sem_match,
                    "code": code_match,
                    "name": year.text,
                    "link": year["href"],
                }
            )
    end_time = time.time()
    return {
        "time": str(round((end_time - start_time), 2)) + "s",
        "list": year_list,
    }
