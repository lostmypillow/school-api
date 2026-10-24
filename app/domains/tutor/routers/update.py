from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core.exec_sql import exec_sql
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.lib.sync_frontend import sync_frontend

router = APIRouter(prefix="/update", tags=["Update tutor details"])


class UpdateTeacherResponse(BaseModel):
    detail: str = Field(default="Update success", description="操作結果訊息")



@router.post(
    "/",
    response_model=UpdateTeacherResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "更新教師資料成功",
        },
    },
)
async def update_teacher_info(cardholder: Cardholder) -> UpdateTeacherResponse:
    await exec_sql(
        "update_teacher_info",
        cardholder.new_school,
        cardholder.card_id,
        cardholder.card_id,
        
    )
    await sync_frontend()

    return UpdateTeacherResponse(detail="Update success")
