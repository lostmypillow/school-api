from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import exec_sql, get_session
import logging
from pprint import pformat

from fastapi import status, Response

# from database.exec_sql import exec_sql
from fastapi.exceptions import HTTPException

from src.services.proxmox import ProxmoxService
from src.services.custom import CustomService
router = APIRouter(
    tags=["Generate vv files"],
)
logger = logging.getLogger("rich")


@router.get("/config/{owner}")
async def get_config(
    owner: str,
    session: AsyncSession = Depends(get_session),
):
    try:
        if owner == "all":
            all_vm_details = await exec_sql("all", "read_all", session=session)
            logger.info("all_vm_details:")
            logger.info(pformat(all_vm_details))
            return all_vm_details
        vm_details = await exec_sql(
            "all",
            "read_for_owner",
            request_owner=owner,
            session=session,
        )
        return vm_details
        logger.info("vm_details:")
        logger.info(pformat(vm_details))
        service = ProxmoxService(vm_details=vm_details[0])
        return service.retrieve_config()
    except Exception:
        logger.exception("VM details not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM details not found",
        )


@router.get("/file/{id}")
async def generate_vv(id: str, session: AsyncSession = Depends(get_session),):
    vm_details = await exec_sql(
        "one",
        "select_by_id",
        id=id,
        session=session
    )
    if vm_details["pve"]:
        service = ProxmoxService(vm_details=vm_details)
    else:
        service = CustomService(vm_details=vm_details)
    config = service.retrieve_config()

    return Response(
        content=config,
        media_type="application/x-virt-viewer",
        headers={"Content-Disposition": 'attachment; filename="console.vv"'}
    )
