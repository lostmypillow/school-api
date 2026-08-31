import logging
import uuid

import httpx
from fastapi import status
from fastapi.exceptions import HTTPException

from app.schemas import ServerErrorDetail, ServerErrorLog

logger = logging.getLogger(__name__)


async def get_http_client():
    try:
        async with httpx.AsyncClient(verify=False) as client:
            yield client
    except httpx.HTTPError as exc:
        error_id = str(uuid.uuid4())
        log_payload = ServerErrorLog(
            reference_id=error_id, message="httpx had an error", detail=str(exc)
        )
        logger.exception(log_payload.model_dump(mode="json"))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ServerErrorDetail(
                reference_id=error_id,
                message="Error while contacting API",
            ).model_dump(mode="json"),
        ) from exc

    except Exception as e:
        error_id = str(uuid.uuid4())
        log_payload = ServerErrorLog(
            reference_id=error_id, message="Undefined error", detail=str(e)
        )
        logger.exception(log_payload.model_dump(mode="json"))

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ServerErrorDetail(
                reference_id=error_id,
                message="Unknown error occurred",
            ).model_dump(mode="json"),
        ) from e
