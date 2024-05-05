import re, requests
from bs4 import BeautifulSoup
from ninja import NinjaAPI

api = NinjaAPI()


@api.get("/sems")
def get_semester(request):
    lst = []
    base_url = "https://aps.ntut.edu.tw/course/tw/courseSID.jsp"
    years = BeautifulSoup(requests.get(base_url).content, "html.parser")
    get_real_year = years.find_all(lambda tag: tag.name == 'a' and tag.get('href', '').startswith('Subj'))
    for g in get_real_year:
        extract_sem_year = re.findall(r'\d+', g.text)

        lst.append({
            "year": extract_sem_year[0],
            "sem": extract_sem_year[1],
        })
    return lst


@api.get("/deps")
def get_departments(request, year, sem):
    lst = []

    def scrape(url):
        return BeautifulSoup(requests.get(url).content, "html.parser").find_all("a")

    base_url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-2&year=" + str(year) + "&sem=" + str(sem)
    data = scrape(base_url)
    for dep in data:
        code = dep['href'][dep['href'].find("code=") + len("code=")]
        lst.append({
            "name": dep.text,
            "link": dep['href'],
            "code": code,
        })
    return lst


@api.get("/years")
def get_years(request, year, sem, code):
    lst = []

    def scrape(url):
        return BeautifulSoup(requests.get(url).content, "html.parser").find_all("a")

    base_url = "https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-3&year=" + str(year) + " &sem=" + str(
        sem) + "&code=" + str(code)
    # https://aps.ntut.edu.tw/course/tw/Subj.jsp?format=-3&year=112&sem=2&code=54
    data = scrape(base_url)
    for year in data:
        lst.append({
            "name": year.text,
            "code": year['href'],
        })
    return lst


# it doesn't return code

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
