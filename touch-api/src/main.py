from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import time
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from typing import List, Optional
from .event_manager import send_event_to_clients, event_stream
import asyncio
from .routers import video, seats, survey, picture, auth
import json
from pydantic import BaseModel, Field
from .database import execute_SQL
from datetime import datetime

from .models.course_model import Course
from fastapi.staticfiles import StaticFiles
# List of clients (queues for SSE connections)
clients: List[asyncio.Queue] = []

# Hold the reference to the main event loop
loop: asyncio.AbstractEventLoop = None


class TodayClass(BaseModel):
    location: str
    name: str
    time: str
    other: int


def get_today_classes():
    # date = datetime.now().strftime('%Y/%m/%d')
    date = '2023/08/15'

    # current_hour = datetime.now().hour
    # if current_hour >= 12 and current_hour <= 17:
    #     period = 2
    # elif current_hour <= 11:
    #     period = 1
    # else:
    #     period = 3
    current_hour = 8
    period = 1

    results = execute_SQL(
        'scheduled_classes',
        'all',
        current_date=date, current_period=period
    )
    classroom_map = [
        ,
        ,
        ,
        ,
        
    ]

    event_message = []
    for result in results:
        result = list(result)  # Convert Row to a list (mutable)
        result[0] = classroom_map[result[0] - 1]  # Modify the classroom

        extracted_hour = datetime.strptime(result[2], "%H:%M").hour
        if extracted_hour > current_hour:
            event_message.append(TodayClass(
                location=result[0], name=result[1], time=result[2], other=result[3]).model_dump())
    return {"type": "today", "data": event_message}
    # [(2, '', '09:00', 1), (3, '', '09:00', 1)]


def get_class_with_seat():
    # def getSeatInfo(self):
    # def is_seat_system_available(self):
    course = Course()
    return  {
            "type": "remaining",
            "data": course.model_dump()
        }
event_data = {"type": None, "data": None}

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global loop
#     loop = asyncio.get_event_loop()  # Get the main event loop at the start
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(get_today_classes, 'interval',
#                       seconds=600)
#     scheduler.add_job(get_today_classes, 'cron',
#                       hour=12, minute=1)
#     scheduler.add_job(get_today_classes, 'cron',
#                       hour=18, minute=1)
#     scheduler.add_job(get_today_classes, 'cron',
#                       hour=0, minute=1)
#     scheduler.add_job(get_class_with_seat, 'interval',
#                       seconds=300)
#     scheduler.add_job(get_class_with_seat, 'interval',
#                       seconds=3)
#     scheduler.start()
#     yield


# Initialize FastAPI app with lifespan (context manager)


# Add CORS middleware to allow frontend communication
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['http://localhost', 'http://localhost:5173'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
]
app = FastAPI(middleware=middleware)
app.mount("/", StaticFiles(directory="public"), name="public")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware to measure request processing time
# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.time()
#     response = await call_next(request)
#     print(f"Request took {time.time() - start_time} sec")
#     return response


@app.get("/events")
async def sse_endpoint():
    """Endpoint for the client to connect via SSE."""
    get_today_classes() # Trigger get_today_classes
    get_class_with_seat()  # Trigger get_class_with_seat
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get('/eventpoll/{type}')
async def event_poll(type: int):
    if type == 0:
        return get_class_with_seat()
    else:
        return get_today_classes()
    



app.include_router(video.router)
app.include_router(seats.router)
app.include_router(survey.router)
app.include_router(picture.router)
app.include_router(auth.router)