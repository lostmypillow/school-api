import logging
import os
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends

from app.dependencies import get_scrape_client
from app.omdb.schemas import OMDBResponse

logger = logging.getLogger(__name__)
load_dotenv()
router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/search/")
async def search_movies(
    query: str, client: Annotated[httpx.AsyncClient, Depends(get_scrape_client)]
) -> OMDBResponse:
    logger.info(f"Query recieved for term {query}")
    url = f"https://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&s={query}"
    r = await client.get(url)
    logger.info(f"OMDB API response: {r}")
    r.raise_for_status()
    validated_data = OMDBResponse.model_validate(r.json())
    return validated_data
