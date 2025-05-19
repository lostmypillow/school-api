import logging
logger = logging.getLogger('uvicorn.error')
import smbclient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from .version import VERSION
from src.database.exec_sql import async_engine, exec_sql
from src.models.device import Device
from src.models.cardholder import Cardholder
from src.config import settings

import traceback
from src.routers.picture import router as picture_router
from src.routers.ws import sync_frontend, router as ws_router
from pprint import pformat

from fastapi.middleware.cors import CORSMiddleware



async def lifespan(app: FastAPI):
    logger.info(f' v{VERSION} starting...')
    smbclient.register_session(
        server=settings.SMB_HOST,
        username=settings.SMB_USERNAME,
        password=settings.SMB_PASSWORD
    )
    smbclient.ClientConfig(timeout=10)

    yield
    if async_engine:
        await async_engine.dispose()

app = FastAPI(
    lifespan=lifespan, # type: ignore
    
    version=VERSION
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.mount("/static", StaticFiles(directory="pictures"), name="pictures")
app.mount("/dash", StaticFiles(directory="public", html=True), name="dashboard")

active_connections: dict[str, WebSocket] = {}


app.include_router(picture_router)
app.include_router(ws_router)

@app.get(
    '/{device_id}/{card_id}',
    responses={
        200: {
            "description": "XXX老師 刷卡成功 | XXX學生 刷卡成功 | 刷卡失敗: XXX",

        }
    }
)
async def register_card_id(device_id: int, card_id: str):
    try:
        cardholder = Cardholder(**await exec_sql(
            "one",
            "fetch_role_student",
            card_id=card_id
        )
        )

        if type(cardholder.name) == str:
            cardholder.role = "student"
            logger.info(
                f"Cardholder is student: {pformat(cardholder.model_dump())}")

        elif cardholder.name == None:
            print("Cardholder is not a student, trying teacher")
            cardholder = Cardholder(**await exec_sql(
                "one",
                "fetch_role_teacher",
                card_id=card_id
            )
            )

            if cardholder.name == None:
                logger.error(f"Error: Can't find info for {card_id}")
                return "刷卡失敗: 查無此人"

            elif type(cardholder.name) == str:
                cardholder.role = "teacher"
                associated_device = await exec_sql(
                    "one",
                    "fetch_associated_device",
                    teacher_id=cardholder.card_id
                )
                if associated_device != {}:
                    cardholder.device_id = associated_device['設備號碼']
                logger.info(
                    f"Cardholder is teacher: {pformat(cardholder.model_dump())}")

        cardholder.card_id = cardholder.card_id.strip()

        if cardholder.role == 'teacher':
            if cardholder.device_id == device_id:
                logger.info(
                    "Cardholder device_id matches incoming device_id, will clear this device and return early")
                await exec_sql(
                    "commit",
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=device_id
                )
                await sync_frontend()
                return f'{cardholder.name}老師 刷卡成功'

            elif cardholder.device_id is not None and cardholder.device_id != device_id:
                logger.info(
                    "Cardholder has a device assigned and it's not this device, will clear DB")
                await exec_sql(
                    "commit",
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=cardholder.device_id
                )
            logger.info(
                "Assigning this device to the teacher and returning early.")
            await exec_sql(
                "commit",
                "register_update_teacher",
                teacher_id=cardholder.card_id,
                device_id=device_id
            )
            await sync_frontend()
            return f'{cardholder.name}老師 刷卡成功'

        elif cardholder.role == 'student':
            device = Device(
                device_id=device_id,
                teacher_id=(
                    await exec_sql(
                        "one",
                        "check_for_teacher",
                        device_id=str(device_id)
                    ))['老師編號']
            )
            logger.info(f'Device info: {pformat(device.model_dump())}')
            if device.teacher_id == None:
                logger.info("Device has no teacher, returning error")
                return '刷卡失敗: 輔導老師未刷卡'

            reservation_id = await exec_sql(
                "one",
                "register_select",
                student_id=cardholder.card_id,
                teacher_id=device.teacher_id
            )
            if reservation_id == {}:
                logger.info(
                    "Student has no reservation ID associated, proceeding to create one")
                await exec_sql(
                    "commit",
                    "register_insert",
                    student_id=cardholder.card_id,
                    teacher_id=device.teacher_id
                )
            else:
                logger.info(
                    "Student has reservation ID, proceeding to update time for end of class")
                await exec_sql(
                    "commit",
                    "register_update_student",
                    reservation_id=reservation_id['自動編號']
                )
            await sync_frontend()
            return f'{cardholder.name}學生 刷卡成功'
    except Exception as e:
        logger.exception(f"[main] Unexpected error:\n{traceback.format_exc()}")
        return '刷卡失敗: API 錯誤'




