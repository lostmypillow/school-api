from pydantic import BaseModel, Field


class UpdateTeacherResponse(BaseModel):
    detail: str = Field(default="Update success", description="操作結果訊息")
