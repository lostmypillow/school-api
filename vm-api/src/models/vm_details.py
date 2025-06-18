from pydantic import BaseModel
from typing import Literal,Union

class VMDetails(BaseModel):
    vm_name: str
    human_owner: str | None
    pc_owner: str | None
    pve: Literal[0, 1]
    pve_host: str | None = None
    pve_token_username: str | None = None
    pve_token_name: str | None = None
    pve_token_value: str | None = None
    pve_vm_id: int | None = None
    proxy_from: str | None = None
    pve_proxy: str | None = None
    spice_proxy: str
    vm_password: str | None = None
    usb: Literal[0, 1]