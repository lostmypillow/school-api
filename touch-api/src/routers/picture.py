from fastapi import APIRouter, Response, HTTPException
from ..database import execute_SQL
router = APIRouter(
    prefix="/picture",
    tags=["Picture"],
)

@router.get('/{role}/{id}',
         responses={
             200: {
                 "content":
                 {
                     "image/png": {}
                 }
             }
         },
         response_class=Response)
def get_employee_image(role: str, id: str):
    # def GetTodayEmployeePhotoByID(self, id):
    try:
        image_bytes = execute_SQL('picture/' + role + '_image', "one", id=id).照片
        return Response(content=image_bytes, media_type="image/png")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
