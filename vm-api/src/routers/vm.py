from fastapi import APIRouter, status, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List
from ..models import VMResponse, ErrorResponse, MessageResponse, VMDetails
from pprint import pformat

# from database.exec_sql import exec_sql
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
import logging
from src.dependencies import exec_sql, get_session

logger = logging.getLogger("rich")
router = APIRouter(
    prefix="/vm",
    tags=["Virtual Machines"],
)


@router.get(
    "/{owner}",
    response_model=Union[List[VMResponse], MessageResponse],
    responses={404: {"model": ErrorResponse}},
    summary="Retrieve VM information for a specific owner or all records",
)
async def return_vm_info(
    owner: str = Path(
        ..., description="Use 'all' to fetch all VMs, or the owner attribute"
    ),
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"owner variable is {owner}")
    try:
        if owner == "all":
            all_vm_details = await exec_sql("all", "read_all", session=session)
            logger.info("all_vm_details:")
            logger.info(pformat(all_vm_details))
            return all_vm_details
        else:
            vm_details = await exec_sql(
                "all", "read_for_owner", request_owner=owner, session=session
            )
            logger.info("vm_details:")
            logger.info(pformat(vm_details))
            return vm_details
    except Exception as e:
        logger.exception("VM details not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VM details not found"
        )


@router.post(
    "/",
    response_model=MessageResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Create New VM",
)
async def create_vm_details(
    vm_details: VMDetails, session: AsyncSession = Depends(get_session)
):
    """
    Insert new VM record into the database.
    """
    try:
        logger.info("vm_details:")
        logger.info(vm_details.model_dump_json(indent=2))
        await exec_sql("commit", "insert", session=session, **vm_details.model_dump())
        return {"message": "ok"}
    except IntegrityError as e:
        logger.exception("IntegrityError raised")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IntegrityError raised"
        )


@router.put(
    "/{id}",
    response_model=MessageResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Update VM by ID",
)
async def update_vm_details(
    id: int, vm_details: VMDetails, session: AsyncSession = Depends(get_session)
):
    """
    Update existing VM entry by its ID.
    """
    try:
        params = vm_details.model_dump()
        logger.info("params:")
        logger.info(vm_details.model_dump_json(indent=2))
        params["id"] = id
        await exec_sql("commit", "update", session=session, **params)
        logger.info("SQL UPDATE Success!")
        return {"message": "ok"}
    except IntegrityError as e:
        logger.exception("IntegrityError raised")
        raise HTTPException(status_code=404, detail="IntegrityError raised")
    except Exception as e:
        logger.exception("Exception raised")
        raise HTTPException(status_code=404, detail="Exception raised")


@router.delete(
    "/{id}",
    summary="Delete a VM entry using its ID",
    response_model=MessageResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_vm_details(id: int, session: AsyncSession = Depends(get_session)):
    try:
        logger.info(f"Deleting VM {str(id)}")
        await exec_sql("commit", "delete", session=session, id=id)
        logger.info("SQL DELETE Success!")
        return {"message": "ok"}
    except Exception as e:
        logging.exception("Exception raised")
        raise HTTPException(status_code=404, detail="Exception raised")
