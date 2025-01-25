from fastapi import APIRouter, Response, HTTPException
from app.database.async_operations import exec_sql
from app.lib.custom_logger import logger
from typing import Literal
picture_router = APIRouter(
    prefix="/picture",
    tags=["Picture"],
)

image_response = {
    200: {
        "content":
        {
            "image/png": {}
        }
    }
}


@picture_router.get('/{role}/{id}',
            responses=image_response,
            response_class=Response)
async def get_image(role: Literal['employee', 'student'], id: str):
    """Gets an image of either an employee or a student

    Parameters
    ----------
    role : Literal[&#39;employee&#39;, &#39;student&#39;]
        Either 'employee' or 'student'
    id : str
        ID of either employee or student
    """
    # def GetTodayEmployeePhotoByID(self, id):
    try:
        image_data = await exec_sql('one', 'picture_' + role, id=id)
        image_bytes = image_data['照片']
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        logger.error(f'[PIC] {e}')
        raise HTTPException(404, 'Image not found')
