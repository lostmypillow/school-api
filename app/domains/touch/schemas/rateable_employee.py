from pydantic import BaseModel, Field


class RateableEmployee(BaseModel):  # noqa: D101
    student_id: str = Field(
        ...,
        pattern=r"^\d{6}$",
        description="員工編號",
    )
    name: str = Field(
        ...,
        description="就...name",
    )
    main_department: str = Field(
        ...,
        description="部門",
    )
