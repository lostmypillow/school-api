# JCourses
A full stack Django/Django Ninja web scraper API that scrapes data from the [NTUT Course Website](https://aps.ntut.edu.tw/course/tw/course.jsp) PLUS a NextJS frontend

[Demo(Planned)](https://jcourses.lostmypillow.duckdns.org)


[API Docs](https://jcourses.lostmypillow.duckdns.org/api/docs)


## Tech Stack
**Django** with **Django Ninja**
Frontend in **NextJS (React)**


## Recreate this Project

```bash
#set up a virtual environment first, then:
pip install -r requirements.txt

./manage.py runserver

#OR

 gunicorn --bind 0.0.0.0:8000 jcourses.wsgi
```

## Features
- API endpoints
- Swagger
- BeautifulSoup web scraping


## Future for this Project

- Mobile App