# JCourses
## What is it?
A Django API that scrapes data from the [NTUT Course Website](https://aps.ntut.edu.tw/course/tw/course.jsp)

Demo (WIP)

[API Docs](https://jcourses.lostmypillow.duckdns.org/api/docs)

[Backup API Docs](https://jcourses.onrender.com/api/docs)
## How does it work?

## Tech Stack
 - **Django** with **Django Ninja** API endpoints
 - Frontend planned


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
