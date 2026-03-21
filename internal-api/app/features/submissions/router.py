import logging
from collections.abc import Sequence
from datetime import date
from typing import Annotated, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import RowMapping, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependecies import get_session

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/trials", tags=["TrialRecords"])

error_message = ""

class TrialRecordBase(BaseModel):
    source: str | None = None
    student_id: str | None = Field(None, pattern=r"^\d{6}$", description="Must be exactly 6 digits if provided")
    student_name: str | None = None
    middle_school_name: str | None = None
    middle_school_class: str | None = None
    high_school_name: str | None = None
    high_school_class: str | None = None
    registered_class: str | None = None
    trial_date: date | None = None
    telephone: str | None = None
    mobile: str | None = None
    notes: str = ""
    parent_name: str | None = None
    manager: str | None = None
    status: str | None = None
    current_grade: str | None= None

    @model_validator(mode="after")
    def check_school_and_contact_requirements(self):  # noqa: ANN201
        if not self.middle_school_name and not self.high_school_name:
            no_school_error_message = "At least one school name (middle_school_name or high_school_name) must be provided."
            raise ValueError(no_school_error_message)

        if not self.telephone and not self.mobile:
            no_phone_error_message = "At least one contact number (telephone or mobile) must be provided."
            raise ValueError(no_phone_error_message)

        return self


class TrialRecordCreate(TrialRecordBase):
    pass


class TrialRecordResponse(TrialRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

@router.get("/managers")
async def get_managers( db: Annotated[AsyncSession, Depends(get_session)]):
    query = text("""
    select
	姓名
from
	.dbo.使用者
where
	是業務 = 1
	AND 狀態 = 1
	AND LEN(學號) >= 6
    """)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=TrialRecordResponse)
async def create_trial(trial: TrialRecordCreate, db: Annotated[AsyncSession, Depends(get_session)]) -> dict:
    query = text("""
        INSERT INTO trial_records
        (source, student_id, student_name, middle_school_name, middle_school_class,
         high_school_name, high_school_class, registered_class, trial_date,
         telephone, mobile, notes, parent_name, manager, status, current_grade,
         created_at, updated_at)
        OUTPUT Inserted.id, Inserted.created_at, Inserted.updated_at
        VALUES
        (:source, :student_id, :student_name, :middle_school_name, :middle_school_class,
         :high_school_name, :high_school_class, :registered_class, :trial_date,
         :telephone, :mobile, :notes, :parent_name, :manager, :status, :current_grade,
         GETDATE(), GETDATE())
    """)

    try:
        result = await db.execute(query, trial.model_dump())
        inserted_row = result.mappings().first()
        await db.commit()
        return {**trial.model_dump(), **inserted_row}
    except IntegrityError as e:
        await db.rollback()
        error_message = f"Database integrity error: {e.orig}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message) from None
    except Exception as e:
        await db.rollback()
        error_message ="An unexpected error occurred while creating the trial."
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message) from e


@router.get("/", response_model=list[TrialRecordResponse])
async def read_trials( db: Annotated[AsyncSession, Depends(get_session)], skip: int = 0, limit: int = 50) -> Sequence[RowMapping]:
    query = text("""
        SELECT id, source, student_id, student_name, middle_school_name, middle_school_class,
               high_school_name, high_school_class, registered_class, trial_date,
               telephone, mobile, notes, parent_name, manager, status, current_grade, created_at, updated_at
        FROM trial_records
        ORDER BY id
        OFFSET :skip ROWS
        FETCH NEXT :limit ROWS ONLY
    """)

    result = await db.execute(query, {"skip": skip, "limit": limit})
    return result.mappings().all()


@router.get("/{trial_id}", response_model=TrialRecordResponse)
async def read_trial(trial_id: int, db: Annotated[AsyncSession, Depends(get_session)]) -> RowMapping:
    query = text("""
        SELECT id, source, student_id, student_name, middle_school_name, middle_school_class,
               high_school_name, high_school_class, registered_class, trial_date,
               telephone, mobile, notes, parent_name, manager, status. current_grade, created_at, updated_at
        FROM trial_records
        WHERE id = :id
    """)

    result = await db.execute(query, {"id": trial_id})
    row = result.mappings().first()

    if not row:
        error_message = "TrialRecord not found"
        logger.exception(error_message, result)
        raise HTTPException(status_code=404, detail=error_message)
    return row


@router.put("/{trial_id}", response_model=TrialRecordResponse)
async def update_trial(trial_id: int, trial: TrialRecordBase, db: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, Any]:
    check_query = text("SELECT id FROM trial_records WHERE id = :id")
    check_result = await db.execute(check_query, {"id": trial_id})
    if not check_result.scalar():
        error_message = "TrialRecord not found"
        logger.exception(error_message, check_result)
        raise HTTPException(status_code=404, detail=error_message)

    update_query = text("""
        UPDATE trial_records
        SET source = :source,
            student_id = :student_id,
            student_name = :student_name,
            middle_school_name = :middle_school_name,
            middle_school_class = :middle_school_class,
            high_school_name = :high_school_name,
            high_school_class = :high_school_class,
            registered_class = :registered_class,
            trial_date = :trial_date,
            telephone = :telephone,
            mobile = :mobile,
            notes = :notes,
            parent_name = :parent_name,
            manager = :manager,
            status = :status,
            current_grade = :current_grade, updated_at = GETDATE()
        OUTPUT Inserted.id, Inserted.created_at, Inserted.updated_at
        WHERE id = :id
    """)

    params = trial.model_dump()
    params["id"] = trial_id

    try:
        result =await db.execute(update_query, params)
        updated_row = result.mappings().first()
        await db.commit()
        return {**trial.model_dump(), **updated_row}
    except IntegrityError as e:
        await db.rollback()
        error_message = f"Database integrity error: {e.orig}"
        logger.exception(error_message)
        raise HTTPException(status_code=400, detail=error_message) from None
    except Exception as e:
        await db.rollback()
        error_message = "An unexpected error occurred while updating the trial."
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message) from e


@router.delete("/{trial_id}")
async def delete_trial(trial_id: int, db: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    query = text("""
        DELETE FROM trial_records
        WHERE id = :id
    """)

    result = await db.execute(query, {"id": trial_id})
    await db.commit()

    if result.rowcount == 0:
        error_message = "TrialRecord not found"
        logger.exception(error_message)
        raise HTTPException(status_code=404, detail=error_message)

    return {"detail": "TrialRecord deleted successfully"}
