from pydantic import BaseModel, ConfigDict


class TutorCreate(BaseModel):
    id: str
    name: str | None = None
    card_id: str | None = None
    college: str | None = None
    new_college: str | None = None
    department: str | None = None
    email: str | None = None


class TutorUpdate(BaseModel):
    id: str | None = None
    name: str | None = None
    card_id: str | None = None
    college: str | None = None
    new_college: str | None = None
    department: str | None = None
    email: str | None = None


class TutorResponse(BaseModel):
    id: str
    name: str | None = None
    card_id: str | None = None
    college: str | None = None
    new_college: str | None = None
    department: str | None = None
    email: str | None = None

    model_config = ConfigDict(from_attributes=True)
