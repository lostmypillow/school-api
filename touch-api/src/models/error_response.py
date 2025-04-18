from pydantic import BaseModel, Field
class ErrorResponse(BaseModel):
    detail: str = Field(..., example="抱歉，系統發生錯誤! Error xxx")
