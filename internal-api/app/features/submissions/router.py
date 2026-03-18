from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependecies import get_session

router = APIRouter(prefix="/submissions", tags=["Submissions"])


class SubmissionBase(BaseModel):
    source: str | None = None
    student_name: str | None = None
    school_name: str | None = None
    school_class: str | None = None
    telephone: str | None = None
    mobile: str | None = None
    notes: str | None = None
    parent_name: str | None = None
    manager: str | None = None
    status: str | None = None


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionResponse(SubmissionBase):
    id: int


@router.post("/", response_model=SubmissionResponse)
async def create_submission(
    submission: SubmissionCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    query = text("""
        INSERT INTO submissions_unified
        (source, student_name, school_name, school_class, telephone, mobile, notes, parent_name, manager, status)
        OUTPUT Inserted.id
        VALUES
        (:source, :student_name, :school_name, :school_class, :telephone, :mobile, :notes, :parent_name, :manager, :status)
    """)

    result = await db.execute(query, submission.model_dump())
    new_id = result.scalar()
    await db.commit()

    return {**submission.model_dump(), "id": new_id}


@router.get("/", response_model=list[SubmissionResponse])
async def read_submissions(
    db: Annotated[AsyncSession, Depends(get_session)], skip: int = 0, limit: int = 50
):
    query = text("""
        SELECT id, source, student_name, school_name, school_class, telephone, mobile, notes, parent_name, manager, status
        FROM submissions_unified
        ORDER BY id
        OFFSET :skip ROWS
        FETCH NEXT :limit ROWS ONLY
    """)

    result = await db.execute(query, {"skip": skip, "limit": limit})
    rows = result.mappings().all()
    return rows


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def read_submission(submission_id: int, db: Annotated[AsyncSession, Depends(get_session)]):
    query = text("""
        SELECT id, source, student_name, school_name, school_class, telephone, mobile, notes, parent_name, manager, status
        FROM submissions_unified
        WHERE id = :id
    """)

    result = await db.execute(query, {"id": submission_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")
    return row


@router.put("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission: SubmissionBase,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    check_query = text("SELECT id FROM submissions_unified WHERE id = :id")
    check_result = await db.execute(check_query, {"id": submission_id})
    if not check_result.scalar():
        raise HTTPException(status_code=404, detail="Submission not found")

    update_query = text("""
        UPDATE submissions_unified
        SET source = :source,
            student_name = :student_name,
            school_name = :school_name,
            school_class = :school_class,
            telephone = :telephone,
            mobile = :mobile,
            notes = :notes,
            parent_name = :parent_name,
            manager = :manager,
            status = :status
        WHERE id = :id
    """)

    params = submission.model_dump()
    params["id"] = submission_id

    await db.execute(update_query, params)
    await db.commit()

    return {**submission.model_dump(), "id": submission_id}


@router.delete("/{submission_id}")
async def delete_submission(submission_id: int, db: Annotated[AsyncSession, Depends(get_session)]):
    query = text("""
        DELETE FROM submissions_unified
        WHERE id = :id
    """)

    result = await db.execute(query, {"id": submission_id})
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {"detail": "Submission deleted successfully"}
