import time

from src.ntut.dependencies import scrape


async def extract_departments(client, year, sem):
    start_time = time.time()
    dep_list = []
    for dep in await scrape(
        client=client,
        url="Subj.jsp?format=-2&year=" + str(year) + "&sem=" + str(sem),
        tag="a",
    ):
        # TODO: resolve type check here
        match = re.search(r"year=(\d+)&sem=(\d+)&code=([A-Za-z\d]+)", dep["href"])
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
