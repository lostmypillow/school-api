from typing import Union

from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database.async_operations import async_engine, exec_sql
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.exc import IntegrityError
from .version import VERSION

async def lifespan(app: FastAPI):
    yield
    if async_engine:
        await async_engine.dispose()

app = FastAPI(lifespan=lifespan, version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/vm/{owner}")
async def return_vm_info( owner: str ):
   

    try:
        if owner == 'all':
            all_vm_details = await exec_sql('all', 'read_all')
            return all_vm_details
        else:
            vm_details = await exec_sql(
                'all',
                'read_for_owner',
                request_owner=owner
            )
            return vm_details
    except Exception as e:
        raise HTTPException(404, 'VM details not found')


@app.post('/vm')
async def create_vm_details(vm_details: VMDetails):
    try:
        await exec_sql(
            'commit',
            'insert',
            **vm_details.model_dump()
        )
        return 'ok'
    except IntegrityError as e:
        raise HTTPException(404, f'{e.orig}')


@app.put('/vm/{id}')
async def update_vm_details(id: int, vm_details: VMDetails):
    try:
        params = vm_details.model_dump()
        params['id'] = id
        await exec_sql(
            'commit',
            'update',
            **params
        )
        return 'ok'
    except IntegrityError or Exception as e:
        raise HTTPException(
            404, f'{e.orig if type(e) == IntegrityError else e}')


@app.delete('/vm/{id}')
async def delete_vm_details(id: int):
    try:
        await exec_sql('commit', 'delete', id=id)
    except Exception as e:
        print(e)
        raise HTTPException(404, 'Error creating')
app.mount("/dash", StaticFiles(directory="public", html=True), name="dash")
