from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.routers.ws import ws_router
from app.routers.auth import auth_router
from app.routers.picture import picture_router
from app.routers.video import video_router
from app.routers.ws import active_connections
from fastapi.staticfiles import StaticFiles
from app.lib.send_updates import send_updates
from pydantic import BaseModel
from app.database.operations import commit_sql, fetch_one_sql
from app.lib.get_dep_number import get_dep_number
from app.database.async_operations import async_engine, exec_sql
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Any, Union
import asyncio
import logging
import uvicorn
from app.lib.sync import sync
from app.lib.custom_logger import logger

class SeatInfo(BaseModel):
    student_id: str
    sn: int


class SurveyInfo(BaseModel):
    employee_id: str
    student_id: str
    rating: int
    dep_number: int





async def lifespan(app: FastAPI):
    logger.info('meow')
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
        logger.info('Disposed async SQLAlchemy Engine')

    if scheduler:
        scheduler.shutdown()
        logger.info('Shut down APScheduler')

    # if smb_session:
    #     smb_session.disconnect()
    #     logger.info('Disconnected SMB Session')


app = FastAPI(


    lifespan=lifespan,

    # Here I define the title. This is purely cosmetic, and so you know which application's Swagger Doc you're looking at when you visit the "/docs" endpoint
    title="觸控螢幕 API /  API",

    # Version is also arbitrary. I wasn't keeping track, and we (Gitea) don't have semantic versioning. I follow the ZeroVer convention by keeping the version number under (and never reaching) 1.0.0
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(video_router)
# app.include_router(picture.router)
app.include_router(auth_router)
app.include_router(ws_router)

# @app.post('/seat')
# def register_seat(seat_info: SeatInfo):
#     """_summary_

#     Parameters
#     ----------
#     seat_info : SeatInfo
#         _description_

#     Raises
#     ------
#     HTTPException
#         _description_
#     """
#     try:
#         commit_sql(
#             'student/register_seat',
#             student_id=seat_info.student_id,
#             sn=seat_info.sn
#         )
#     except Exception as e:
#         print(e)
#         raise HTTPException(404, '發生錯誤')


# @app.post('/rate')
# def rate_employee(survey_info: SurveyInfo):
#     try:
#         commit_sql(
#             'rate_employee',
#             student_id=survey_info.student_id,
#             department=get_dep_number(survey_info.employee_id),
#             employee_id=survey_info.employee_id,
#             rank=survey_info.rating
#         )
#     except Exception as e:
#         print(e)
#         raise HTTPException(404, '發生錯誤')


@app.get('/test')
async def test():
    deps = {
        : 2,
        "": 4,
        : 8,
        : 9,
        : 11
    }

    emp_working_today = await exec_sql(
        'all',
        'student_today_employees',
        current_date='2020-09-16'
    )
    for employee in emp_working_today:
        if "學號" in employee:
            employee['學號'] = employee['學號'].strip()
        #
        if '主要部門' in employee:
            employee['主要部門'] = next(
                (k for k, v in deps.items() if v == employee['主要部門']), None)

    voted_emp_week = await exec_sql(
        'all',
        'student_voted_employees',
        monday='2020-12-15 00:00:00.000',
        student_id=''
    )

    return [y for y in emp_working_today if y['學號'] not in {x['評分對象'] for x in voted_emp_week}]
