## JCourses

### What is it?

A Django API that scrapes data from the [NTUT Course Website](https://aps.ntut.edu.tw/course/tw/course.jsp)

Demo (WIP)

[API Docs](https://jcourses.lostmypillow.duckdns.org/api/docs)

[Backup API Docs](https://jcourses.onrender.com/api/docs)

### How does it work?

#### Tech Stack

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

# JSearch0 Backend

> This is a prototype website, denoted by the 0 in the name "JSearch0". Expect bugs.

> This is the repository for the FastAPI backend, if you're looking for JSearch0 API's GitHub repository, it's
> here: https://github.com/lostmypillow/jsearch

## What is it?

![image](https://github.com/user-attachments/assets/84740b26-ff7c-4f75-837e-4f2ebd6bebb5)

- A full stack search engine for movies and Google search. Consumes OMDb API and a rate limited RapidAPI that returns
  Google search results.

- Works with the API hosted on Render.

- Features dark/light mode switch.

- [**Demo website**](https://jsearch0.chodanpillow.com)

- [**API Documentation**](https://jsearch-api.onrender.com/docs)

## How does it work?

1. User inputs a value in Vue frontend
2. Frontend navigates to search path and sends the data to the FastAPI server
3. FastAPI server sends back the results
4. Vue frontend displays the results

## Tech Stack

- **FastAPI** API endpoints
- **Nuxt(Vue)** frontend x **Vuetify** components

### lint

```bash
uv run ruff check .
```

### formatter

```
uv run ruff format --check .
```

### init pyrefly

uv run pyrefly init

### add pre-commit

uvx pre-commit install

### dev server

```
uv run fastapi dev src/main.py

uv run cdk synth

# Type check (ensures CDK construct types/props match)
uv run pyright

# Fast linting and syntax checking
uv run ruff check .
```

Core only (Base dependencies without dev tools or AWS)
Bash

uv sync --no-dev

Core-Dev (Base dependencies + dev tools, excludes AWS)
Bash

uv sync --only-group core-dev

AWS (Base dependencies + AWS optional extra, no dev tools)
Bash

```
uv sync --no-dev --extra aws
```
AWS-Dev (Base dependencies + dev tools + AWS extra)
Bash

```
uv sync --only-group aws-dev
uv run --env-file .env.local python -m app.worker
```
