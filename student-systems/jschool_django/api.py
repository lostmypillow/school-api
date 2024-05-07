import re, requests
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
    sem_list = []
    sems = scrape(combine("courseSID.jsp"), "")
    for sem in sems:
        extract_sem_year = re.findall(r'\d+', sem.text)
        sem_list.append({
            "year": extract_sem_year[0],
            "sem": extract_sem_year[1],
            "link": sem['href'],
        })
    print(time)
    return sem_list


@api.get("/deps")
def get_departments(request, link):
    dep_list = []
    deps = scrape(combine(link))
    for dep in deps:
        dep_list.append({
            "name": dep.text,
            "link": dep['href'],
        })
    return dep_list


@api.get("/years")
def get_years(request, link):
    year_list = []
    # https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-3&year=112&sem=2&code=54
    years = scrape(combine(link))
    for year in years:
        year_list.append({
            "name": year.text,
            "link": year['href'],
        })
    return year_list


@api.get("/course")
def get_course(request):
    lst = []
    uurl = "Subj.jsp?format=-4&year=112&sem=2&code=2683"
    course_data = scrape(combine(uurl), "td")
    x = course_data.text.replace(" ", "").replace("　", "").split("\n")
    stripx = [line.strip() for line in x if line.strip()]
    matches = [i for i, item in enumerate(stripx) if re.match(r'\b\d{6}\b', item)]
    grouped_text = [stripx[matches[i]:matches[i + 1]] for i in range(len(matches) - 1)] + [stripx[matches[-1]:]]
    return {"text": grouped_text}

