from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
# from .cardholder import Cardholder
# from .device import Device
from .version import VERSION
from typing import Optional
from src.database.exec_sql import async_engine, exec_sql
from src.models.device import Device
from src.models.cardholder import Cardholder
from src.models.fetch_role import FetchRoleResponse
# from fastapi.responses import PlainTextResponse
# from typing import Literal, Union
# Entry of the FastAPI app


async def lifespan(app: FastAPI):
    yield
    if async_engine:
        await async_engine.dispose()
app = FastAPI(
    lifespan=lifespan,
    title="高偉數學輔導系统",
    version=VERSION
)

app.mount("/dash", StaticFiles(directory="public", html=True), name="dashboard")

# This stores the websocket connections used in @app.websocket("/ws") in this file.
#
# This only exists because I wanted to pass the websocket connection to other classes/files.
active_websocket: Optional[WebSocket] = None


# If you're wondering why card_id is a string and not an integer, it's cuz card IDs have letters in them.
#
# If you have a better idea of making sure the endpoint only gets card numbers and not some other arbitary string, go for it.

@app.get('/{device_id}/{card_id}')
async def test(device_id: int, card_id: str):
    cardholder = Cardholder(**await exec_sql(
        "one",
        "fetch_role_student",
        card_id=card_id
    )
    )
    if type(cardholder.name) == str:
        cardholder.role = "student"

    elif cardholder.name == None:
        print("Not a student, trying teacher")
        cardholder = Cardholder(**await exec_sql(
            "one",
            "fetch_role_teacher",
            card_id=card_id
        )
        )

        if cardholder.name == None:
            # not found throw error
            print("Not found")
        elif type(cardholder.name) == str:
            cardholder.role = "teacher"
            associated_device = await exec_sql(
                "one",
                "fetch_associated_device",
                teacher_id=cardholder.card_id
            )
            if associated_device != {}:
                cardholder.device_id = associated_device['設備號碼']

    cardholder.card_id = cardholder.card_id.strip()

    if cardholder.role == 'teacher':
        if cardholder.device_id == device_id:
            # If the device matches, clear this device and stop further processing
            await exec_sql(
                "commit",
                "register_update_teacher",
                teacher_id=None,
                device_id=device_id
            )
            return f'{cardholder.name}老師 刷卡成功'
        #  If cardholder has a device assigned and it's not this device
        elif cardholder.device_id is not None and cardholder.device_id != device_id:
            # Clear the DB of the cardholder's old device
            await exec_sql(
                "commit",
                "register_update_teacher",
                teacher_id=None,
                device_id=cardholder.device_id
            )
        # Finally, assign this device to the cardholder
        await exec_sql(
            "commit",
            "register_update_teacher",
            teacher_id=cardholder.card_id,
            device_id=device_id
        )
        return f'{cardholder.name}老師 刷卡成功'

    # if cardholder.role == 'student':
    #     print('is student')
    #     device = Device(
    #         device_id=device_id,
    #         teacher_id=(
    #             await exec_sql(
    #                 "one",
    #                 "check_for_teacher",
    #                 device_id=str(device_id)
    #             ))['老師編號']

    #     )
    #     if device.teacher_id:
    #         #  device has teacher, proceed
    #     else:
    #         # device has no teacher, throw error
    #     print(device)

    return cardholder

    # return


# @app.get(
#     '/{device_id}/{card_id}',
#     response_class=PlainTextResponse,
#     responses= {
#         200: {
#             "description": "Success message",
#             "model": Union[Literal["OK"], str]
#         }
#     }
# )
# async def process_card(card_id: str, device_id: int):
#     """Processes card ID based on a given device ID / 根據給的裝置 ID 處理卡號

#     Parameters
#     ----------
#     card_id : str
#         card ID from RPi device / 來自樹梅派的卡號

#     device_id : int
#         device ID of the RPi device / 樹梅派裝置ID

#     Returns
#     -------
#     str
#         message to be sent for display on the RPi / 要顯示在樹梅派 GUI 上的訊息
#     """
#     try:

#         # Initializes a Device instance. See device.py in the src folder for more details.
#         device = Device(device_id)

#         # Initializes a Cardholder instance. See cardholder.py in the src folder for more details.
#         cardholder = Cardholder(card_id)

#         # Calls the register function of the Device instance. *Sigh* you know where to look for more details.
#         await device.register(cardholder, active_websocket)

#         # Sends the message back to the Pi
#         return device.message

#     except Exception as e:

#         # I don't have any bright ideas for logging errors. So I just print it.
#         print(str(e))

#         # This error message will be sent to and displayed on the Pi.
#         return "刷卡失敗"


# Websocket connection to communicate with _vue, the frontend running on the (currently planned) TV screen.
#
# Yes, I do know that a better way would be server sent events, since the TV doesn't really send anything back. But if it ain't broke I'm not fixing it.
#
#  Have a go at it if you can.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Sends real time info on which teacher is associated with which device / 傳送哪位老師在哪個裝置的即時資訊

    Parameters
    ----------
    websocket : WebSocket
        The websocket instance
    """

    # Uses the active_websocket variable at the beginning of this file
    global active_websocket

    # Waits for...the client to accept? Idk, VSCode is not showing the docs for the accept() method dammit.
    await websocket.accept()

    # Sets the current connection as the  active websocket connection
    active_websocket = websocket

    # For every device (1-6, and also this only runs once when the client connects)...
    for n in range(1, 7):

        # Initialize a Device class.
        device = Device(n)

        # If the device IS associated with a teacher...
        if device.teacher_id is not None:

            # Initialize a Cardholder instance of that teacher
            teacher = Cardholder(device.teacher_id)

            # Sends the details of that teacher to the device
            await websocket.send_json(
                {
                    "device": device.id,
                    "image": teacher.id,
                    "teacher": teacher.name,
                    "school": teacher.school
                }
            )

    # This recieves messages from the client but completely useless for the reason detailed above @app.websocket("/ws")
    try:
        while True:
            message = await websocket.receive_text()

    # Handles client disconnection
    except WebSocketDisconnect:
        active_websocket = None
