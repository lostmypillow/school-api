from pydantic import BaseModel
from typing import List
from .vm_response import VMResponse


class VMListResponse(BaseModel):
    vms: List[VMResponse]
