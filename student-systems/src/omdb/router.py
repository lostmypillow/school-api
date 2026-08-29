import os
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from src.dependencies import get_http_client

load_dotenv()
router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/health")
async def check_health(client: Annotated[httpx.AsyncClient, Depends(get_http_client)]):
    url = f"https://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&s=Thor"
    await client.get(url)
    return "success"

@router.get("/search/")
async def search_movies(
    query: str, client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
):
    url = f"https://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&s={query}"
    r = await client.get(url)
    return {"results": r.json()}
