from fastapi import APIRouter

import logging
from pprint import pformat

from fastapi import status, Response

from fastapi.exceptions import HTTPException

from app.core.exec_psql import exec_mssql_async
from app.domains.vm.services.proxmox import ProxmoxService
from app.domains.vm.services.custom import CustomService
router = APIRouter(
    tags=["Generate vv files"],
)
logger = logging.getLogger("__name__")


@router.get("/config/{owner}")
async def get_config(
    owner: str,
):
    try:
        if owner == "all":
            all_vm_details = await exec_mssql_async("vm/read_all")
            logger.info("all_vm_details:")
            logger.info(pformat(all_vm_details))
            return all_vm_details
        vm_details = await exec_mssql_async(
            "read_for_owner",
            owner
        )
        return vm_details
    except Exception:
        logger.exception("VM details not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM details not found",
        )


@router.get("/file/{id}")
async def generate_vv(vm_id: str ):
    vm_details_list = await exec_mssql_async("vm/select_by_id", vm_id)
    if len(vm_details_list) != 1 :
        raise ValueError("More than one VM details matched")
    vm_details = vm_details_list[0]
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
