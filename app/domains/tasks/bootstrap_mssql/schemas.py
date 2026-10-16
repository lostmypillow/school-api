from pydantic import BaseModel, ConfigDict, Field


class BootstrapSummaryModel(BaseModel):
    """Structured summary schema for MSSQL database bootstrapping counts."""

    model_config = ConfigDict(extra="forbid")

    semesters: int = Field(default=0, description="Total semester records synced")
    departments: int = Field(default=0, description="Total department records synced")
    department_years: int = Field(default=0, description="Total department-year records synced")
    courses: int = Field(default=0, description="Total course records synced")
    courses_syllabi: int = Field(default=0, description="Total course syllabus records synced")
