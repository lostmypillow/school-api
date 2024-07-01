from enum import Enum

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
origins = [
     "http://localhost:32773",
     "http://localhost:32774",
     "http://localhost:32778",
     "http://localhost:32777",
     "http://localhost:3000",
    
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/get-movies/")
async def get_movies(query: str):
    print("yest")
    url = f"https://www.omdbapi.com/?apikey=e9cb394&s={query}"

    r = httpx.get(url)
    print(r)
    print(r.headers['content-type'])

    return {"results": r.json()}


@app.get("/get-google/")
async def get_google(query: str, limit: int, related: bool):
    url = f'https://google-search74.p.rapidapi.com/?query={query}&limit={limit}&related_keywords={related}'
    headers = {
        "X-RapidAPI-Key": "4cc2304fb3msh28544a85c39f266p17c92bjsnd635c2ee140a",
        "X-RapidAPI-Host": "google-search74.p.rapidapi.com",
    }
    r = httpx.get(url, headers=headers)

    print(r.json())

    return {"results": r.json()}

app.mount("/", StaticFiles(directory="static", html=True), name="static")