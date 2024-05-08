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
        return BeautifulSoup(requests.get(combined_url).content, "html.parser").find_all(str(tag))


@api.get("/sems")
def get_semester(request):
    start_time = time.time()
    sem_list = []
    sems = scrape("courseSID.jsp", "sem")
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
    deps = scrape(link, "a")
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
    years = scrape(link, "a")
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
    combined_url = "https://aps.ntut.edu.tw/course/tw/" + uurl
    find = BeautifulSoup(requests.get(combined_url).content, "lxml").find_all("tr")

    count = 0
    for f in find:
        #     # print(f"Row {count}: {f}")
        cells = BeautifulSoup(str(f), 'lxml').find_all("td")
        count += 1
        print(f"number{count}: {cells}")
        try:
            course = {
                "code": cells[0].text.strip() if cells[0].text.strip() else None,
                "name": cells[1].text.strip() if cells[1].text.strip() else None,
                "credits": (cells[2].text.strip()) if cells[2].text.strip() else None,
                "type": cells[5].text.strip() if cells[5].text.strip() else None,
                "professor": cells[6].text.strip() if cells[6].text.strip() else None,
                "time1": cells[9].text.strip() if cells[9].text.strip() else None,
                "time2": cells[10].text.strip() if cells[10].text.strip() else None,
                "ppl": int(cells[15].text.strip()) if cells[15].text.strip() else None,
                "ppldrop": int(cells[16].text.strip()) if cells[16].text.strip() else None,
                "lang": cells[18].text.strip() if cells[18].text.strip() else None,
                "link": cells[19].find('a')['href'] if cells[19].find('a') else None,
                "notes": cells[20].text.strip() if cells[20].text.strip() else None,
            }
            lst.append(course)
        except IndexError:
            print("empty list")


    #     alt_count = 0
    #     for tt in s:
    #         print(f"Row {alt_count}, s = {str(tt.text)}")
    #         alt_count += 1
    #     count += 1
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
        "list": lst,
    }
