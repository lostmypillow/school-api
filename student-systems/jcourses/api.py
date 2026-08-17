import re, requests
import time
from bs4 import BeautifulSoup
from ninja import NinjaAPI

api = NinjaAPI()


def scrape(url, tag):
    combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
    if tag == "sem":
        return BeautifulSoup(requests.get(combined_url).content, "html.parser").find_all(
            lambda tag: tag.name == 'a' and tag.get('href', '').startswith('Subj'))
    else:
        return BeautifulSoup(requests.get(combined_url).content, "lxml").find_all(str(tag))
        


@api.get("/sems")
def get_semester(request):
    start_time = time.time()
    sem_list = []
    for sem in scrape("courseSID.jsp", "sem"):
        extract_sem_year = re.findall(r'\d+', sem.text)
        sem_list.append({
            "year": extract_sem_year[0],
            "sem": extract_sem_year[1],
            "link": sem['href'],
        })
    end_time = time.time()
    return {
        "time": str(end_time - start_time) + " seconds",
        "list": sem_list,
    }


@api.get("/deps")
def get_departments(request, year, sem):
    start_time = time.time()
    dep_list = []
    for dep in scrape("Subj.jsp?format=-2&year=" + str(year) + "&sem=" + str(sem), "a"):
        match = re.search(r"year=(\d+)&sem=(\d+)&code=([A-Za-z\d]+)", dep['href'])
        dep_list.append({
            "year": match.group(1),
            "sem": match.group(2),
            "code": match.group(3),
            "name": dep.text,
            "link": dep['href'],
        })
    end_time = time.time()
    return {
        "time": str(end_time - start_time) + " seconds",
        "list": dep_list,
    }


@api.get("/years")
def get_years(request, year, sem, code):
    start_time = time.time()
    year_list = []
    for year in scrape("Subj.jsp?format=-3&year=" + str(year) + "&sem=" + str(sem) + "&code=" + str(code), "a"):
        match = re.search(r"year=(\d+)&sem=(\d+)&code=(\d+)", year['href'])
        year_match = match.group(1)
        sem_match = match.group(2)
        code_match = match.group(3)
        year_list.append({
            "year": year_match,
            "sem": sem_match,
            "code": code_match,
            "name": year.text,
            "link": year['href'],
        })
    end_time = time.time()
    return {
        "time": str(end_time - start_time) + " seconds",
        "list": year_list,
    }


@api.get("/course")
def get_course(request, year, sem, code):
    start_time = time.time()
    course_list = []
    for f in scrape("Subj.jsp?format=-4&year=" + str(year) + "&sem=" + str(sem) + "&code=" + str(code),"tr"):
        cells = BeautifulSoup(str(f), 'lxml').find_all("td")
        try:
            course_list.append({
                "code": cells[0].text.strip() if cells[0].text.strip() else None,
                "name": cells[1].text.strip() if cells[1].text.strip() else None,
                "credits": (cells[2].text.strip()) if cells[2].text.strip() else None,
                "type": cells[5].text.strip() if cells[5].text.strip() else None,
                "prof": cells[6].text.strip() if cells[6].text.strip() else None,
                "sun": cells[7].text.strip() if cells[7].text.strip() else None,
                "mons": cells[8].text.strip() if cells[8].text.strip() else None,
                "tues": cells[9].text.strip() if cells[9].text.strip() else None,
                "wed": cells[10].text.strip() if cells[10].text.strip() else None,
                "thu": cells[11].text.strip() if cells[11].text.strip() else None,
                "fri": cells[12].text.strip() if cells[12].text.strip() else None,
                "sat": cells[13].text.strip() if cells[13].text.strip() else None,
                "classroom": cells[14].text.strip() if cells[14].text.strip() else None,
                "ppl": int(cells[15].text.strip()) if cells[15].text.strip() else None,
                "dropped_ppl": int(cells[16].text.strip()) if cells[16].text.strip() else None,
                "lang": cells[17].text.strip() if cells[17].text.strip() else None,
                "link": cells[18].find('a')['href'] if cells[18].find('a') else None,
                "notes": cells[19].text.strip() if cells[19].text.strip() else None,
                "with_class": cells[20].text.strip() if cells[20].text.strip() else None,
                "experiment": cells[21].text.strip() if cells[21].text.strip() else None,
                "cross_disp": cells[22].text.strip() if cells[22].text.strip() else None,
            })
        except IndexError:
            course_list.append({
                "error": "IndexError"
            })
    end_time = time.time()
    return {
        "time": str(end_time - start_time) + " seconds",
        "list": course_list,
        }
