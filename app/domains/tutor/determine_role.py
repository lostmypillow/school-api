from typing import cast
import logging

logger: logging.Logger = logging.getLogger(__name__)

from app.core.db import exec_mssql_async
from app.domains.tutor.models import Cardholder
from app.domains.tutor.schemas import StudentSqlRow, TeacherSqlRow, AssociatedDeviceSqlRow


async def determine_role(card_id: str) -> Cardholder | str:
    """Determine role (student vs teacher) based on card_id and return Cardholder or error string."""
    # 1. Check if cardholder is student (matches card_id or student_id)
    student_rows: list[StudentSqlRow] | None = cast(
        list[StudentSqlRow] | None,
        await exec_mssql_async("fetch_role_student", card_id, card_id),
    )
    if student_rows:
        row: StudentSqlRow = student_rows[0]
        cardholder: Cardholder = Cardholder(**row)
        cardholder.role = "student"
        cardholder.card_id = (
            cardholder.card_id.strip() if cardholder.card_id is not None else cardholder.card_id
        )
        logger.info("Cardholder is student: %s", cardholder.model_dump_json(indent=2))
        return cardholder

    # 2. Check if cardholder is teacher (matches card_id or id)
    logger.info("Cardholder is not a student, trying teacher")
    teacher_rows: list[TeacherSqlRow] | None = cast(
        list[TeacherSqlRow] | None,
        await exec_mssql_async("fetch_role_teacher", card_id, card_id),
    )
    if not teacher_rows:
        logger.error("Error: Can't find info for %s", card_id)
        return "刷卡失敗: 查無此人"

    teacher_row: TeacherSqlRow = teacher_rows[0]
    cardholder = Cardholder(**teacher_row)
    cardholder.role = "teacher"

    device_rows: list[AssociatedDeviceSqlRow] | None = cast(
        list[AssociatedDeviceSqlRow] | None,
        await exec_mssql_async("fetch_associated_device", cardholder.card_id),
    )
    if device_rows:
        cardholder.device_id = device_rows[0].get("id")

    cardholder.card_id = (
        cardholder.card_id.strip() if cardholder.card_id is not None else cardholder.card_id
    )
    logger.info("Cardholder is teacher: %s", cardholder.model_dump_json(indent=2))
    return cardholder
