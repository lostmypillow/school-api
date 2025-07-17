"""錯誤回傳資訊.


"""
from pydantic import BaseModel


class ErrorResponse(BaseModel):  # noqa: D101
    detail: str
