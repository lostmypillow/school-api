import re
import time

from app.ntut.dependencies import scrape


async def extract_departments(client, year, sem):
    start_time = time.time()
    dep_list = []
    for dep in await scrape(
        client=client,
        url="Subj.jsp?format=-2&year=" + str(year) + "&sem=" + str(sem),
        tag="a",
    ):
        href = str(dep["href"])
        match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", href)
        if match:
            dep_list.append(
                {
                    "year": match.group(1),
                    "sem": match.group(2),
                    "code": match.group(3),
                    "name": dep.text,
                    "link": dep["href"],
                }
            )
    end_time = time.time()
    return {
        "time": str(round((end_time - start_time), 2)) + "s",
        "list": dep_list,
    }
