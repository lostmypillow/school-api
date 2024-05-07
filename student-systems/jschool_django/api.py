import re, requests
import time

from bs4 import BeautifulSoup
from ninja import NinjaAPI

api = NinjaAPI()

base_url = "https://aps.ntut.edu.tw/course/tw/"


def combine(url):
    return base_url + str(url)


def scrape(url, tag):
    if tag == "td":
        return BeautifulSoup(requests.get(url).content, "html.parser").find(str(tag))

    elif tag != "":
        return BeautifulSoup(requests.get(url).content, "html.parser").find_all(str(tag))
    else:
        return BeautifulSoup(requests.get(url).content, "html.parser").find_all(
            lambda tag: tag.name == 'a' and tag.get('href', '').startswith('Subj'))


@api.get("/sems")
def get_semester(request):
    start_time = time.time()
    sem_list = []
    sems = scrape(combine("courseSID.jsp"), "")
    for sem in sems:
        extract_sem_year = re.findall(r'\d+', sem.text)
        sem_list.append({
            "year": extract_sem_year[0],
            "sem": extract_sem_year[1],
            "link": sem['href'],
        })
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    return sem_list


@api.get("/deps")
def get_departments(request, link):
    start_time = time.time()
    dep_list = []
    deps = scrape(combine(link))
    for dep in deps:
        dep_list.append({
            "name": dep.text,
            "link": dep['href'],
        })
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    return dep_list


@api.get("/years")
def get_years(request, link):
    start_time = time.time()
    year_list = []
    # https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-3&year=112&sem=2&code=54
    years = scrape(combine(link))
    for year in years:
        year_list.append({
            "name": year.text,
            "link": year['href'],
        })
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    return year_list


@api.get("/course")
def get_course(request):
    start_time = time.time()
    lst = []
    uurl = "Subj.jsp?format=-4&year=112&sem=2&code=2913"
    course_data = scrape(combine(uurl), "td")
    print(course_data)
    x = course_data.text.replace(" ", "").replace("　", "").split("\n")
    stripx = [line.strip() for line in x if line.strip()]
    matches = [i for i, item in enumerate(stripx) if re.match(r'\b\d{6}\b', item)]
    grouped_text = [stripx[matches[i]:matches[i + 1]] for i in range(len(matches) - 1)] + [stripx[matches[-1]:]]
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(elapsed_time)
    return {"text": "yo"}

@api.get("/course_new")
def get_course_new(request):
    start_time = time.time()
    lst = []
    uurl = "Subj.jsp?format=-4&year=112&sem=2&code=2913"
    course_data = scrape(combine(uurl), "tr")
    # for row in course_data:
    #     cells = row.find_all('td')
    #     course = {
    #         "code": cells[0].text.strip() if cells[0].text.strip() else None,
    #         "name": cells[1].text.strip() if cells[1].text.strip() else None,
    #         "credits": float(cells[2].text.strip()) if cells[2].text.strip() else None,
    #         "type": cells[5].text.strip() if cells[5].text.strip() else None,
    #         "professor": cells[6].text.strip() if cells[6].text.strip() else None,
    #         "time1": cells[9].text.strip() if cells[9].text.strip() else None,
    #         "time2": cells[10].text.strip() if cells[10].text.strip() else None,
    #         "ppl": int(cells[15].text.strip()) if cells[15].text.strip() else None,
    #         "ppldrop": int(cells[16].text.strip()) if cells[16].text.strip() else None,
    #         "lang": cells[18].text.strip() if cells[18].text.strip() else None,
    #         "link": cells[19].find('a')['href'] if cells[19].find('a') else None,
    #         "notes": cells[20].text.strip() if cells[20].text.strip() else None
    #     }
    #     lst.append(course)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return {
        "time": elapsed_time,
        "text": course_data,
    }
