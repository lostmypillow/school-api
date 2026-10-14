from datetime import date

from pydantic import BaseModel, Field, model_validator


class TrialRecordBase(BaseModel):
    source: str | None = None
    student_id: str | None = Field(
        None,
        pattern=r"^\d{6}$",
        description="若有提供, 則必須剛好為 6 位數字。",
    )
    student_name: str | None = None
    middle_school_name: str | None = None
    middle_school_class: str | None = None
    high_school_name: str | None = None
    high_school_class: str | None = None
    registered_class: str | None = None
    trial_date: date | None = None
    telephone: str | None = None
    mobile: str | None = None
    notes: str = ""
    parent_name: str | None = None
    manager: str | None = None
    status: str | None = None
    current_grade: str | None = None

    @model_validator(mode="after")
    def check_school_and_contact_requirements(self):  # noqa: ANN201
        if not self.middle_school_name and not self.high_school_name:
            no_school_error_message = "必須提供至少一個學校名稱(國中校名或高中校名)。"
            raise ValueError(no_school_error_message)

        if not self.telephone and not self.mobile:
            no_phone_error_message = "必須提供至少一個聯絡電話 (市話或手機)。"
            raise ValueError(no_phone_error_message)

        return self
