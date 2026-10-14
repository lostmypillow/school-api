from fastapi import APIRouter, HTTPException, Path, status

from app.core.exec_mssql_async import exec_mssql_async
from app.domains.tutor.process_card import process_card
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.lib.sync_frontend import sync_frontend
from app.domains.tutor.schemas.update_teacher_response import UpdateTeacherResponse

router: APIRouter = APIRouter(prefix="/card", tags=["Card Swipe"])


@router.get(
    "/{device_id}/{card_id}",
    response_model=Cardholder | str,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "XXX老師 刷卡成功 | XXX學生 刷卡成功 | 刷卡失敗: XXX",
        },
        404: {
            "description": "Not found for device 0",
        },
        500: {
            "description": "Internal Server Error",
        },
    },
)
async def register_card_id(
    device_id: int = Path(..., ge=0, le=6, description="device ID (0: teacher lookup, 1..6: card swipe)"),
    card_id: str = Path(..., min_length=1, max_length=50, description="cardholder ID"),
) -> Cardholder | str:
    try:
        result = await process_card(device_id, card_id)
        if result is None:
            raise
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post(
    "/update",
    response_model=UpdateTeacherResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "更新教師資料成功",
        },
    },
)
async def update_teacher_info(cardholder: Cardholder) -> UpdateTeacherResponse:
    await exec_mssql_async(
        "update_teacher_info",
        cardholder.new_school,
        cardholder.card_id,
        cardholder.card_id,
        fetch=False,
    )
    await sync_frontend()

    return UpdateTeacherResponse(detail="Update success")
