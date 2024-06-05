# JCourses
A Django/Django Ninja web scraper + API that scrapes data from the [NTUT Course Website](https://aps.ntut.edu.tw/course/tw/course.jsp)

[API Docs](https://lostmypillow.pythonanywhere.com/api/docs)


## Tech Stack
**Django** with **Django Ninja**


## Recreate this Project

```bash
#set up a virtual environment first, then:
pip install -r requirements.txt

./manage.py runserver

#OR

 gunicorn --bind 0.0.0.0:8000 jcourses.wsgi
```

## Backend Concepts Used
- Set API endpoints
- Swagger (NinjaAPI skin)
- BeautifulSoup web scraping
- JSON serialization


## Why is it hosted on PythonAnywhere?/Where's the demo website?
I haven't set up my homelab. After I set it up I will be able to host it on better hardware and a custom domain. The frontend is also forthcoming to consume this API.


## Future for this Project

### Frontend
An API needs a frontend, duh!

### Mobile App
Speaking of frontend, mobile app version of said frontend is also planned.