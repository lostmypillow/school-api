import logging
from typing import Any, cast

from fastapi import HTTPException, status

from app.core.exec_mssql_async import exec_mssql_async
from app.domains.tutor.determine_role import determine_role
from app.domains.tutor.lib.sync_frontend import sync_frontend
from app.domains.tutor.schemas.cardholder import Cardholder
from app.domains.tutor.schemas.device import Device
from app.domains.tutor.schemas.appointment_sql import AppointmentSqlRow
from app.domains.tutor.schemas.check_device_teacher import CheckDeviceTeacherSqlRow

logger: logging.Logger = logging.getLogger(__name__)

async def process_card(device_id: int, card_id: str) -> str | None | Any:
    """Process a card swipe for a given device and card ID."""
    try:
        cardholder: Cardholder | str = await determine_role(card_id=card_id)
        if not isinstance(cardholder, Cardholder):
            if device_id == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Not found for device 0",
                )
            return cardholder

        if device_id == 0 and cardholder.role == "teacher":
            return cardholder

        if cardholder.role == "teacher":
            if cardholder.device_id == device_id:
                logger.info(
                    "Cardholder device_id matches incoming device_id",
                )
                await exec_mssql_async(
                    "register_update_teacher",
                    None,
                    device_id,
                    fetch=False,
                )
                logger.info("Clearing device and return early")
                await sync_frontend()
                return f"{cardholder.name}老師 刷卡成功"

            if cardholder.device_id is not None and cardholder.device_id != device_id:
                logger.info(
                    "Cardholder has a device assigned and it's not this device, will clear DB",
                )
                await exec_mssql_async(
                    "register_update_teacher",
                    None,
                    cardholder.device_id,
                    fetch=False,
                )
            logger.info("Assigning this device to the teacher and returning early.")
            await exec_mssql_async(
                "register_update_teacher",
                cardholder.card_id,
                device_id,
                fetch=False,
            )
            await sync_frontend()
            return f"{cardholder.name}老師 刷卡成功"

        if cardholder.role == "student":
            rows: list[CheckDeviceTeacherSqlRow] | None = cast(
                list[CheckDeviceTeacherSqlRow] | None,
                await exec_mssql_async("check_for_teacher", device_id),
            )
            teacher_id: str | None = rows[0]["teacher_id"] if rows else None

            device: Device = Device(
                device_id=device_id,
                teacher_id=teacher_id,
            )
            logger.info("Device info: %s", device.model_dump_json(indent=2))
            if device.teacher_id is None:
                logger.info("Device has no teacher, returning error")
                return "刷卡失敗: 輔導老師未刷卡"

            reservation_rows: list[AppointmentSqlRow] | None = cast(
                list[AppointmentSqlRow] | None,
                await exec_mssql_async(
                    "register_select",
                    cardholder.card_id,
                    device.teacher_id,
                ),
            )
            if not reservation_rows:
                logger.info(
                    "Student has no reservation ID associated, proceeding to create one"
                )
                await exec_mssql_async(
                    "register_insert",
                    cardholder.card_id,
                    device.teacher_id,
                    fetch=False,
                )
            else:
                logger.info(
                    "Student has reservation ID, proceeding to update time for end of class"
                )
                appt_id: int = reservation_rows[0]["id"]
                await exec_mssql_async(
                    "register_update_student",
                    appt_id,
                    fetch=False,
                )
            await sync_frontend()
            return f"{cardholder.name}學生 刷卡成功"
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return "刷卡失敗: API 錯誤"
