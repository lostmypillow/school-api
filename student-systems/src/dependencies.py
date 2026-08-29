import httpx
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE


async def get_http_client():
    try:
        async with httpx.AsyncClient() as client:
            yield client
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error while contacting OMDB API: {exc}",
        )

    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error: {e}",
        )
    
