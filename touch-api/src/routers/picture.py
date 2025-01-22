from fastapi import APIRouter, Response, HTTPException
from database.operations import fetch_one_sql
router = APIRouter(
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


@router.get('/{role}/{id}',
            responses=image_response,
            response_class=Response)
def get_employee_image(role: str, id: str):
    """_summary_

    Parameters
    ----------
    role : str
        _description_
    id : str
        _description_
    
    Returns
    -------
    Response
        A custom FastAPI Response class with media_type as PNG

    """
    # def GetTodayEmployeePhotoByID(self, id):
    try:
        image_bytes = fetch_one_sql('picture_' + role, id=id).照片
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Unexpected error: {e}")
