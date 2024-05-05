import re
import time

import requests
from bs4 import BeautifulSoup
from ninja import NinjaAPI

api = NinjaAPI()


@api.get("/hello")
def hello(request):
    return "Hello world"


@api.get("/year")
def get_year_and_semester(request):
    start_time = time.time()
    lst = []
    base_url = "https://aps.ntut.edu.tw/course/tw/courseSID.jsp"
    years = BeautifulSoup(requests.get(base_url).content, "html.parser")
    get_real_year = years.find_all(lambda tag: tag.name == 'a' and tag.get('href', '').startswith('Subj'))
    for g in get_real_year:
        dep_list = []
        pattern = r'\d+'
        find_sem = re.findall(pattern, g.text)
        basee = "https://aps.ntut.edu.tw/course/tw/" + g['href']
        get_deps = BeautifulSoup(requests.get(basee).content, "html.parser").find_all("a")
        for dep in get_deps:
            year_list = []
            start_index = dep['href'].find("code=")
            code = dep['href'][start_index + len("code="):]
            base4 = "https://aps.ntut.edu.tw/course/tw/" + dep['href']
            get_year = BeautifulSoup(requests.get(base4).content, "html.parser").find_all("a")
            for ye in get_year:
                start_index = ye['href'].find("code=")
                code = ye['href'][start_index + len("code="):]
                year_list.append({
                    "name": ye.text,
                    "link": ye['href'],
                    "code": code,
                })
            dep_list.append({
                "name": dep.text,
                "code": code,
                "link": dep['href'],
                "years": year_list,
            })
        lst.append({
            "year": find_sem[0],
            "sem": find_sem[1],
            "link": dep_list
        })
    end_time = time.time()
    scraping_time = end_time - start_time
    print(f"Scraping time: {scraping_time} seconds")
    return lst


@api.get("/course")
def get_course(request):
    lst = []
    base_url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-4&year=112&sem=2&code=2683"
    course_data = BeautifulSoup(requests.get(base_url).content, "html.parser").find('td')
    x = course_data.text
    y = x.replace(" ", "").replace("　", "")
    text_list = y.split("\n")

    # Remove empty strings from the list
    items = [line.strip() for line in text_list if line.strip()]
    matches = [i for i, item in enumerate(items) if re.match(r'\b\d{6}\b', item)]

    # Group the text between each sequence of six numbers
    grouped_text = [items[matches[i]:matches[i + 1]] for i in range(len(matches) - 1)] + [items[matches[-1]:]]

    # Print the resulting list
    return {"text": grouped_text}
