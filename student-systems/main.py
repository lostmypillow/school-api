import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
origins = [
    "https://jsearch-latest.onrender.com",
    "https://jsearch.lostmypillow.duckdns.org",
    "https://lostmypillow.github.io",
    "http://localhost:3000",
    "https://jsearch.pages.dev",
    "https://jsearch0.chodanpillow.com/"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["GET"]
)

@app.get("/health")
async def check_health():
    return "success"

@app.get("/get-movies/")
async def get_movies(query: str):
    url = f"https://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&s={query}"
    r = httpx.get(url)
    return {"results": r.json()}


@app.get("/get-google/")
async def get_google(query: str, limit: int, related: bool):
    url = f'https://google-search74.p.rapidapi.com/?query={query}&limit={limit}&related_keywords={related}'
    headers = {
        "X-RapidAPI-Key": os.getenv('RAPIDAPI_API_KEY'),
        "X-RapidAPI-Host": "google-search74.p.rapidapi.com",
    }
    r = httpx.get(url, headers=headers)

    print(r.json())

    return {"results": r.json()}
