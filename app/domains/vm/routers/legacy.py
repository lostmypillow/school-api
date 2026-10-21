from fastapi import APIRouter, status, Path
from typing import Union, List

from app.core.exec_psql import exec_mssql_async
from ..schemas import VMResponse, ErrorResponse, MessageResponse, VMDetails
from pprint import pformat

# from database.exec_sql import exec_sql
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger("__name__")
router = APIRouter(
    tags=["Virtual Machines"],
)


@router.get(
    path="/{owner}",
    response_model=Union[List[VMResponse], MessageResponse],
    responses={404: {"model": ErrorResponse}},
    summary="Retrieve VM information for a specific owner or all records",
)
async def return_vm_info(
    owner: str = Path(
        default=..., description="Use 'all' to fetch all VMs, or the owner attribute"
    )
):
    logger.info(f"owner variable is {owner}")
    try:
        if owner == "all":
            all_vm_details = await exec_mssql_async("vm/read_all")
            logger.info("all_vm_details:")
            logger.info(pformat(all_vm_details))
            return all_vm_details
        else:
            vm_details = await exec_mssql_async("vm/read_for_owner", owner)
            logger.info("vm_details:")
            logger.info(pformat(vm_details))
            return vm_details
    except Exception:
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
    vm_details: VMDetails
):
    """
    Insert new VM record into the database.
    """
    try:
        logger.info("vm_details:")
        logger.info(vm_details.model_dump_json(indent=2))
        await exec_mssql_async("commit", "insert", *vm_details.model_dump().values())
        return {"message": "ok"}
    except IntegrityError:
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
    vm_id: int, vm_details: VMDetails
):
    """
    Update existing VM entry by its ID.
    """
    try:
        await exec_mssql_async("vm/update",  vm_details.model_dump().values(), vm_id)
        logger.info("SQL UPDATE Success!")
        return {"message": "ok"}
    except IntegrityError:
        logger.exception("IntegrityError raised")
        raise HTTPException(status_code=404, detail="IntegrityError raised")
    except Exception:
        logger.exception("Exception raised")
        raise HTTPException(status_code=404, detail="Exception raised")


@router.delete(
    "/{id}",
    summary="Delete a VM entry using its ID",
    response_model=MessageResponse,
    responses={404: {"model": ErrorResponse}},
)
async def delete_vm_details(vm_id: int):
    try:
        logger.info(f"Deleting VM {str(vm_id)}")
        await exec_mssql_async( "vm/delete", vm_id)
        logger.info("SQL DELETE Success!")
        return {"message": "ok"}
    except Exception:
        logging.exception("Exception raised")
        raise HTTPException(status_code=404, detail="Exception raised")
