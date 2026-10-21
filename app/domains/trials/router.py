import logging
from collections.abc import Sequence
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status



from app.core.exec_sql import exec_sql
from app.domains.trials.schemas.log_record_create import LogRecordCreate
from app.domains.trials.schemas.log_record_response import LogRecordResponse
from app.domains.trials.schemas.trial_record_base import TrialRecordBase
from app.domains.trials.schemas.trial_record_create import TrialRecordCreate
from app.domains.trials.schemas.trial_record_response import TrialRecordResponse

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/trials", tags=["TrialRecords"])


@router.post(path="/log", response_model=LogRecordResponse)
async def create_log(
        log_entry: LogRecordCreate,
):
    try:
        result = await exec_sql("trials/create_log", log_entry.model_dump().values())
        logger.info(result)
    except Exception as e:
        logger.exception(msg="Exception occurred", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Exception occurred") from None


@router.get(path="/schools")
async def get_schools(
    level: Literal["middle", "high"] = "middle",
):
    level_id = 2 if level == "middle" else 3

    result = await exec_sql("trials/get_schools", {"level_id": level_id})
    return result


@router.get(path="/managers")
async def get_managers() -> Sequence[Any]:
    result = await exec_sql(command_name="trials/get_managers")
    return result


@router.post(path="/", response_model=TrialRecordResponse)
async def create_trial(
    trial: TrialRecordCreate,
):
    try:
        return await exec_sql("trials/create_trial", trial.model_dump().values())


    except Exception as e:
        error_message = f"建立試用時發生非預期的錯誤。{e}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message) from e


@router.get(path="/")
async def read_trials(skip: int = 0, limit: int = 50):

    result = await exec_sql("read_trials", skip, limit)
    total = result[0]["total_count"] if result else 0

    return {
        "data": result,
        "total": total,
    }


@router.get(path="/{trial_id}", response_model=TrialRecordResponse)
async def read_trial(
    trial_id: int,
):

    row = await exec_sql("trials/read_trial", trial_id)

    if not row:
        error_message = "找不到問課紀錄 (TrialRecord)"
        logger.error("找不到問課紀錄 (TrialRecord): %s", row)
        raise HTTPException(status_code=404, detail=error_message)
    return row


@router.put(path="/{trial_id}", response_model=TrialRecordResponse)
async def update_trial(
    trial_id: int, trial: TrialRecordBase
):
    check_result = await exec_sql("trials/check_trial", trial_id)
    if not check_result:
        error_message = "找不到問課紀錄 (TrialRecord)"
        logger.exception(error_message, check_result)
        raise HTTPException(status_code=404, detail=error_message)

    try:
        result = await exec_sql("trials/update_trial", trial.model_dump().values())
        return result

    except Exception as e:
        error_message = "An unexpected error occurred while updating the trial."
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message) from e


@router.delete("/{trial_id}")
async def delete_trial(trial_id: int) -> dict[str, str]:


    result = await exec_sql("trials/delete_trial", trial_id)

    if not result:
        error_message = "找不到問課紀錄 (TrialRecord)"
        logger.exception(error_message)
        raise HTTPException(status_code=404, detail=error_message)

    return {"detail": "TrialRecord deleted successfully"}
