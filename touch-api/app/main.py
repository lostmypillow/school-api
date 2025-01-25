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
from app.routers.video import sync
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
    class_with_seats: dict[str, Union[str, list[str]]] = await exec_sql('one', 'single_get_remaining')

    # convert 位子, which is a string with a lot of commas, into a list
    # SQ.座位號,
    # SQ.座位
    class_with_seats['座位'] = [
        {"座位": seat, "號碼": seat_num}
        for seat, seat_num in zip(
            class_with_seats['座位'].split(','),
            class_with_seats['座位號'].split(',')
        )
    ]

    class_with_seats['男座位'] = []
    class_with_seats['女座位'] = []
    for seat in class_with_seats['座位']:
        if int(seat["座位"][-2:]) <= 15:
            class_with_seats['女座位'].append(seat)
        else:
            class_with_seats['男座位'].append(seat)
            
    del class_with_seats['座位']
    del class_with_seats['座位號']

    return class_with_seats



# {
#   "主檔號": 4,
#   "班級名稱": "",
#   "班別": "",
#   "座位": [
#     {
#       "座位": "A09",
#       "號碼": "55154"
#     },
#     {
#       "座位": "A13",
#       "號碼": "55155"
#     },
#     {
#       "座位": "A15",
#       "號碼": "55156"
#     },
#     {
#       "座位": "B08",
#       "號碼": "55157"
#     },
#     {
#       "座位": "B11",
#       "號碼": "55158"
#     },
#     {
#       "座位": "B15",
#       "號碼": "55159"
#     },
#     {
#       "座位": "C11",
#       "號碼": "55160"
#     },
#     {
#       "座位": "D10",
#       "號碼": "55161"
#     },
#     {
#       "座位": "E09",
#       "號碼": "55162"
#     },
#     {
#       "座位": "E11",
#       "號碼": "55163"
#     },
#     {
#       "座位": "G09",
#       "號碼": "55164"
#     },
#     {
#       "座位": "G14",
#       "號碼": "55165"
#     },
#     {
#       "座位": "H10",
#       "號碼": "55166"
#     },
#     {
#       "座位": "I15",
#       "號碼": "55167"
#     },
#     {
#       "座位": "I13",
#       "號碼": "55168"
#     },
#     {
#       "座位": "A22",
#       "號碼": "55170"
#     },
#     {
#       "座位": "B21",
#       "號碼": "55171"
#     },
#     {
#       "座位": "B23",
#       "號碼": "55172"
#     },
#     {
#       "座位": "B18",
#       "號碼": "55173"
#     },
#     {
#       "座位": "D22",
#       "號碼": "55174"
#     },
#     {
#       "座位": "E22",
#       "號碼": "55175"
#     },
#     {
#       "座位": "F18",
#       "號碼": "55176"
#     },
#     {
#       "座位": "F23",
#       "號碼": "55177"
#     },
#     {
#       "座位": "H17",
#       "號碼": "55178"
#     },
#     {
#       "座位": "H21",
#       "號碼": "55179"
#     },
#     {
#       "座位": "I20",
#       "號碼": "55180"
#     },
#     {
#       "座位": "I22",
#       "號碼": "55181"
#     },
#     {
#       "座位": "J18",
#       "號碼": "55182"
#     },
#     {
#       "座位": "J22",
#       "號碼": "55183"
#     }
#   ]
# }