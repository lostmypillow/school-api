from pydantic import BaseModel, Field
from typing import Optional
class FetchRoleResponse(BaseModel):
    name: Optional[str] = Field(None, alias="姓名")
    card_id: Optional[str] = Field(None, alias="學號")
