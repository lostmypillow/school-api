import re
import time

from src.ntut.dependencies import scrape


async def extract_semesters(client):
    start_time = time.time()
    sem_list = []
    for sem in await scrape(client=client, url="course.jsp", tag="sem"):
        extract_sem_year = re.findall(r"\d+", sem.text)
        sem_list.append(
            {
                "year": extract_sem_year[0],
                "sem": extract_sem_year[1],
                "link": sem["href"],
            }
        )
    end_time = time.time()
    return {
        "time": str(round((end_time - start_time), 2)) + "s",
        "list": sem_list,
    }
