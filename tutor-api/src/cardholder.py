from .database.operations import execute_SQL
class Cardholder:
    """Class containing cardholder related attributes and methods

    Attributes
    ----------
    role :
        Can be either 'student' or 'teacher'.

    id :
        學號

    name:
        Name, duh!

    school:
        For teachers. School they graduated from.

    device_id:
        Number of the device that this teacher has already scanned.

    Methods
    -------
    _fetch_role(card_id: str):
        Determines the role of the cardholder
    """

    def __init__(self, card_id):
        self.role = None
        """Can be either 'student' or 'teacher'.
        """
        self.id = None
        """學號
        """
        self.name = None
        """Name, duh!
        """
        self.school = None
        """For teachers. School they graduated from.
        """
        self.device_id = None
        """Number of the device that this teacher has already scanned.
        """

        # Fetches role upon initialization.
        self._fetch_role(card_id)
        

    def _fetch_role(self, card_id: str):
        """Determines the role of the cardholder

        Parameters
        ----------
        card_id : str
            The card ID sent from Pi
        """

        # Checks if the cardholder is a student..
        student = execute_SQL(
            "fetch_role_student",
            card_id=card_id
        )

        # If they are...
        if student:

            # ...update details
            self.role = "student"
            self.name = student.姓名.strip()
            self.id = student.學號.strip()

       
        else:

            # If not, we check if they're a teacher...    
            teacher = execute_SQL(
                "fetch_role_teacher",
                card_id=card_id
            )

            # If the cardholder is a teacher...
            if teacher:

                # ...update details.
                self.role = "teacher"
                self.name = teacher.姓名.strip()
                self.id = teacher.學號.strip()
                self.school = teacher.大學.strip()

                # check if the teacher is associated with a device...
                device_result = execute_SQL(
                    "fetch_associated_device",
                    teacher_id=teacher.學號
                    )
                
                #...and update accordingly.
                self.device_id = device_result.設備號碼 if device_result and device_result.設備號碼 is not None else None
            
            else:

                # if card ID isn't associated with anyone, update with arbitrary values
                self.role = "other"
                self.name = "Not Found"
                self.id = "Not Found"