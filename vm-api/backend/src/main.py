from typing import Union, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Literal
import logging
from sqlalchemy.exc import IntegrityError
from database.exec_sql import async_engine, exec_sql
from .version import VERSION


# -----------------------
# Define Response Schemas
# -----------------------
class VMDetails(BaseModel):
    vm_name: str
    human_owner: str | None
    pc_owner: str | None
    pve: int = Literal[0, 1]
    pve_host: str | None = None
    pve_token_username: str | None = None
    pve_token_name: str | None = None
    pve_token_value: str | None = None
    pve_vm_id: int | None = None
    proxy_from: str | None = None
    pve_proxy: str | None = None
    spice_proxy: str
    vm_password: str | None = None
    usb: int = Literal[0, 1]



class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class VMResponse(VMDetails):
    id: int


class VMListResponse(BaseModel):
    vms: List[VMResponse]


# -----------------------
# FastAPI App Setup
# -----------------------
async def lifespan(app: FastAPI):
    yield
    if async_engine:
        await async_engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    version=VERSION,
    title="Kaowei VM",
   
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# API Endpoints
# -----------------------

@app.get("/", response_model=MessageResponse, summary="Root Test Endpoint")
def read_root():
    """Health check endpoint."""
    return {"message": "Hello World"}


@app.get("/vm/{owner}", response_model=Union[List[VMResponse], MessageResponse], responses={404: {"model": ErrorResponse}}, summary="Fetch VM Info")
async def return_vm_info(owner: str):
    """
    Retrieve VM information for a specific owner or all records.
    - `owner`: use `'all'` to fetch all VMs, or a specific name to filter.
    """
    try:
        if owner == 'all':
            all_vm_details = await exec_sql('all', 'read_all')
            return all_vm_details
        else:
            vm_details = await exec_sql('all', 'read_for_owner', request_owner=owner)
            return vm_details
    except Exception as e:
        raise HTTPException(status_code=404, detail="VM details not found")


@app.post("/vm", response_model=MessageResponse, responses={404: {"model": ErrorResponse}}, summary="Create New VM")
async def create_vm_details(vm_details: VMDetails):
    """
    Insert new VM record into the database.
    """
    try:
        await exec_sql('commit', 'insert', **vm_details.model_dump())
        return {"message": "ok"}
    except IntegrityError as e:
        raise HTTPException(status_code=404, detail=str(e.orig))


@app.put("/vm/{id}", response_model=MessageResponse, responses={404: {"model": ErrorResponse}}, summary="Update VM by ID")
async def update_vm_details(id: int, vm_details: VMDetails):
    """
    Update existing VM entry by its ID.
    """
    try:
        params = vm_details.model_dump()
        params['id'] = id
        await exec_sql('commit', 'update', **params)
        return {"message": "ok"}
    except IntegrityError as e:
        raise HTTPException(status_code=404, detail=str(e.orig))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/vm/{id}", response_model=MessageResponse, responses={404: {"model": ErrorResponse}}, summary="Delete VM by ID")
async def delete_vm_details(id: int):
    """
    Delete a VM entry using its ID.
    """
    try:
        await exec_sql('commit', 'delete', id=id)
        return {"message": "ok"}
    except Exception as e:
        logging.info(e)
        raise HTTPException(status_code=404, detail="Error deleting")


# -----------------------
# Static Files (Frontend)
# -----------------------
app.mount("/dash", StaticFiles(directory="public", html=True), name="dash")