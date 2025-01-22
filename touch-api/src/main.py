from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from routers import video, picture, auth
from routers.video import smb_session
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from database.operations import commit_sql, fetch_one_sql
from lib.get_dep_number import get_dep_number
from database.async_operations import async_engine, exec_sql
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Any, Union
import asyncio


class SeatInfo(BaseModel):
    student_id: str
    sn: int


class SurveyInfo(BaseModel):
    employee_id: str
    student_id: str
    rating: int
    dep_number: int


async def send_updates():

    # current_date = datetime.now().strftime('%Y/%m/%d')
    # current_hour = datetime.now().hour
    # match current_hour:
    #     case h if 12 <= h <= 17:
    #         current_period = 2
    #     case h if h <= 11:
    #         current_period = 1
    #     case _:
    #         current_period = 3

    current_date = '2023/08/15'  # DEBUG USE
    current_period = 1  # DEBUG USE

    classes_today: list[dict[str, Any]] = await exec_sql(
        'all',
        'classes_today',
        current_date=current_date,
        current_period=current_period
    )

    # '位子'
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

    del class_with_seats['座位號']

    data = {
        "classes_today": classes_today,
        "class_with_seats": class_with_seats
    }

    if 'client' in active_connections:
        await active_connections['client'].send_json(data)

    print(data)
    print("meow")


async def send_heartbeat():
    if 'control' in active_connections:
        await active_connections['control'].send_json(
            {
                "to": "control",
                "from": "server",
                "action": "heartbeat"
            })


async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.start()
    # scheduler.add_job(
    #     send_updates,
    #     "interval",
    #     seconds=5

    # )

  
    yield
    if async_engine:
        await async_engine.dispose()

    if scheduler:
        scheduler.shutdown()

    if smb_session:
        smb_session.disconnect()


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

# Store connected clients
active_connections: dict[str, WebSocket] = {}


@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await websocket.accept()
    active_connections[client_name] = websocket

    try:
        while True:
            data: dict = await websocket.receive_json()
            if "to" in data:
                recipient = data['to']
                if recipient in active_connections:
                    await active_connections[recipient].send_json(data)
    except WebSocketDisconnect:
        print(f"Client {client_name} disconnected.")
    finally:
        # Ensure the connection is removed from the active connections
        active_connections.pop(client_name, None)
        print(f"Removed {client_name} from active connections.")

        # x= {
        #     "to": "control",
        #     "action": "request"
        # }
        # y = {
        #     "to": "client",
        #     "action": "send",
        #     "data": "meow"
        # }


app.include_router(video.router)
# app.include_router(picture.router)
app.include_router(auth.router)


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
