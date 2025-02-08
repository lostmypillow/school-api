from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.routers.ws import ws_router
from src.routers.auth import auth_router
from src.routers.picture import picture_router
from src.routers.video import video_router
from src.routers.ws import active_connections
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.lib.get_dep_number import get_dep_number
from src.database.async_operations import async_engine, exec_sql
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Any, Union
from src.lib.get_class_with_seats import get_class_with_seats
from src.lib.get_classes_today import get_classes_today
from src.routers.video import sync
from src.lib.custom_logger import logger
from dotenv import load_dotenv
from src.lib.deps import deps
from .config import settings
from pprint import pprint
pprint(settings)

class RegisterSeat(BaseModel):
    學號: str
    號碼: int


class SurveyInfo(BaseModel):
    employee_id: str
    employee_dep: str
    student_id: str
    rating: int


async def send_updates():
    if active_connections:
        for con in active_connections:
            await active_connections[con].send_json(
                {
                    "action": "update class",
                    "message": {
                        "classes_today": await get_classes_today(),
                        "class_with_seats": await get_class_with_seats()
                    }
                }
            )


async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    await sync()
    scheduler.add_job(
        send_updates,
        "interval",
        seconds=5
    )

    yield
    if async_engine:
        await async_engine.dispose()
        logger.info('[SHUTDOWN] Disposed async SQLAlchemy Engine')

    if scheduler:
        scheduler.shutdown()
        logger.info('[SHUTDOWN] Shut down APScheduler')


app = FastAPI(
    lifespan=lifespan,
    title="觸控螢幕 API /  API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(video_router)
app.include_router(picture_router)
app.include_router(auth_router)
app.include_router(ws_router)


@app.post('/seat')
async def register_seat(seat_info: RegisterSeat):
    """_summary_

    Parameters
    ----------
    seat_info : SeatInfo
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    try:
        await exec_sql(
            'commit',
            'register_seat',
            student_id=seat_info.學號,
            sn=seat_info.號碼
        )
    except Exception as e:
        logger.error(f'[SEAT] {e}')
        raise HTTPException(404, '發生錯誤')


@app.post('/rate')
async def rate_employee(survey_info: SurveyInfo):
    global deps
    try:
        await exec_sql(
            'commit',
            'rate_employee',
            student_id=survey_info.student_id,
            department=deps[survey_info.employee_dep],
            employee_id=survey_info.employee_id,
            rating=survey_info.rating
        )
    except Exception as e:
        logger.error(f'[RATE ERROR] {e}')
        raise HTTPException(404, '發生錯誤')


@app.get('/test')
async def test():
    return {
        "action": await get_classes_today(),
    }


app.mount("/dash", StaticFiles(directory="public", html=True), name="dash")
app.mount("/static", StaticFiles(directory="static"), name="static")
