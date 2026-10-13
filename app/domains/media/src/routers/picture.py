from fastapi import APIRouter, Response, HTTPException, Path, Depends, status
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from src.dependencies import exec_sql, get_session
import logging
from time import perf_counter
logger = logging.getLogger("__name__")

router = APIRouter(
    prefix="/picture",
    tags=["Picture"],
)


@router.get(
    "/{role}/{id}",
    summary="Get picture by role and ID",
    description="Retrieves a PNG image of either an employee or a student based on the given role and ID.",
    responses={
        200: {
            "description": "Image is found, and returned as binary/PNG",
            "content": {"image/png": {}},
        },
        404: {
            "description": "Image not found or something, I don't know why it just says 'photo_bytes' for Exception if it doesn't find any, so I use 'Image not found'",
            "content": {"application/json": {"example": {"detail": "Image not found"}}},
        },
    },
    response_class=Response,
)
async def get_image(
    role: Literal["employee", "student"] = Path(
        ..., description="Role, either 'employee' or 'student'"
    ),
    id: str = Path(..., description="The ID of the employee or student, e.g. 300003"),
    session: AsyncSession = Depends(get_session),
):
    """Gets an image of either an employee or a student

    Parameters
    ----------
    role : Literal[&#39;employee&#39;, &#39;student&#39;]
        Either 'employee' or 'student'
    id : str
        ID of either employee or student
    """
    # def GetTodayEmployeePhotoByID(self, id):
    t1_start = perf_counter() 
    try:
        image_data = await exec_sql("one", f"picture_{role}", id=id, session=session)
        t1_stop = perf_counter()

        logger.info(f"Elapsed time: {t1_stop, t1_start}") 


        logger.info(f"Elapsed time during the whole program in seconds: {t1_stop-t1_start}s")
        return Response(content= image_data["photo_bytes"], media_type="image/png")
    except Exception as e:
        logger.exception(f"Image not found")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
