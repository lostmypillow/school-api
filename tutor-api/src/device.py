from .database.operations import execute_SQL
from .cardholder import Cardholder
from fastapi import WebSocket

class Device:
    """Class containing device related attributes and methods

    Attributes
    ----------
    teacher_id : str
        The teacher associated with this device.
    id : int
        
    message: str
        Message to be sent back to the Pi.

    Methods
    -------
    _check_db_exists():
        Check if the device info table exists.

    _check_for_teacher():
        Check if device is associated with a teacher.

    register(cardholder: Cardholder, websocket: WebSocket):
        registers the cardholder to DB, be it teacher or student
    """
    

    def __init__(self, device_id: int):
        self.teacher_id = None
        """The teacher associated with this device.
        """
        self.id: int = device_id
        """The device ID. Could be 1-6."""
        self.message: str = ""
        """ Message to be sent back to the Pi.
        """

        # Runs these private functions on initialization.
        self._check_table_exists()
        self._check_for_teacher()

    def _check_table_exists(self):
        """Check if the device info table exists.
        """
        execute_SQL("check_device_db")

    def _check_for_teacher(self):
        """Check if device is associated with a teacher.
        """

        # If a teacher had already scanned their card against a given device, the executeSQL will return the teacher_id 
        device_teacher_data = execute_SQL(
            "check_for_teacher",
            device_id=self.id
        )
        
        # If there is a teacher ID associated with this device, this func will update the initialized object's teacher_id attribute. If there isn't, this function ends up doing nothing.
        if device_teacher_data and device_teacher_data is not None:
            self.teacher_id = device_teacher_data.老師編號

    async def register(self, cardholder: Cardholder, websocket: WebSocket):
        """registers a given cardholder to db, and also sends updated data to WebSocket if applicable

        Args:
            cardholder (Cardholder): the initialized Cardholder instance
            websocket (WebSocket): the current websocket connection to the TV frontend
        """

        # Self explanatory. If cardholder is a student and a teacher has yet to be associated with this device, this function returns early and sends the below message to the Pi.
        if cardholder.role == "student" and self.teacher_id == None:
            self.message = '刷卡失敗: 輔導老師未刷卡'

        # If cardholder is a student and the device IS associated with a teacher...
        elif cardholder.role == "student" and self.teacher_id is not None:

            # Writes that data to DB
            reservation_id = execute_SQL(
                "register_select",
                student_id=cardholder.id,
                teacher_id=self.teacher_id
            )


            # If student has never scanned in, this func will fire the insert command first. This indicates they started class.
            if not reservation_id or reservation_id == None:
                execute_SQL(
                    "register_insert",
                    student_id=cardholder.id,
                    teacher_id=self.teacher_id
                )
                self.message = f'{cardholder.name}學生 刷卡成功'

            # If the student HAS scanned this device before (meaning the students has ended the class), we update the DB of the time they ended class.
            else:
                execute_SQL(
                    "register_update_student",
                    reservation_id=reservation_id.自動編號
                )
                self.message = f'{cardholder.name}學生 刷卡成功'

        # If the cardholder is a teacher...self explanatory c'mon lol
        elif cardholder.role == "teacher":

            # Check if the cardholder's device is this device (self.id)
            if cardholder.device_id == self.id:

                # If the device matches, clear this device and stop further processing
                execute_SQL(
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=self.id
                )

                # Also clear data from TV frontend via websocket
                if websocket is not None:
                    await websocket.send_json({
                        "device": self.id,
                        "image": "",
                        "teacher": "",
                        "school": ""
                    })

                self.message = f'{cardholder.name}老師 刷卡成功'
                return

            # If cardholder has a device assigned and it's not this device
            elif cardholder.device_id is not None and cardholder.device_id != self.id:

                # Clear the DB of the cardholder's old device
                execute_SQL(
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=cardholder.device_id
                )

                # Make sure it's cleared from the frontend as well
                if websocket is not None:
                    await websocket.send_json({
                        "device": cardholder.device_id,
                        "image": "",
                        "teacher": "",
                        "school": ""
                    }
                    )

            # Finally, assign this device to the cardholder
            execute_SQL(
                "register_update_teacher",
                teacher_id=cardholder.id,
                device_id=self.id
            )

            # Update the TV frontend as well
            if websocket is not None:
                await websocket.send_json(
                    {
                        "device": self.id,
                        "image": cardholder.id,
                        "teacher": cardholder.name,
                        "school": cardholder.school
                    }
                )

            self.message = f'{cardholder.name}老師 刷卡成功'

        else:

            # If cardholder is neither teacher or student, send a generic fail command.
            self.message = '刷卡失敗: 查無此號'
