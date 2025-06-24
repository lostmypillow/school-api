
from pydantic import BaseModel, Field


class FetchRoleResponse(BaseModel):
    name: str | None = Field(None, alias="姓名")
    card_id: str | None = Field(None, alias="學號")
