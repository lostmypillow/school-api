from pydantic import BaseModel


class SchoolRecord(BaseModel):
    id: int
    name: str
    city: str
