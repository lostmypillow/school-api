"""成功回傳資訊.


"""
from pydantic import BaseModel


class SuccessMessage(BaseModel):  # noqa: D101
    message: str = "success"
