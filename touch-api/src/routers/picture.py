from fastapi import APIRouter, Response, HTTPException, Path
from typing import Literal
from src.database.exec_sql import exec_sql
from ..logger import logger
router = APIRouter(
    prefix="/picture",
    tags=["Picture"],
)


@router.get('/{role}/{id}',
                    summary="Get picture by role and ID",
                    description="Retrieves a PNG image of either an employee or a student based on the given role and ID.",
                    responses={
                        200: {
                            "description": "Image is found, and returned as binary/PNG",
                            "content":
                            {
                                "image/png": {}
                            }
                        },
                        404: {
                            "description": "Image not found or something, I don't know why it just says '照片' for Exception if it doesn't find any, so I use 'Image not found'",
                            "content": {
                                "application/json": {
                                    "example": {"detail": "Image not found"}
                                }
                            }
                        }
                    },
                    response_class=Response)
async def get_image(
    role: Literal['employee',
                  'student'] = Path(..., description="Role, either 'employee' or 'student'"),
    id: str = Path(...,
                   description="The ID of the employee or student, e.g. ")
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
    try:
        image_data = await exec_sql('one', 'picture_' + role, id=id)
        # print(type(image_data))
        # return "ok"
        image_bytes = image_data['照片']
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        print(e)
        logger.error(f'[PIC] {e}')
        raise HTTPException(404, 'Image not found')
