from datetime import datetime

from app.domains.trials.schemas.log_record_create import LogRecordCreate


class LogRecordResponse(LogRecordCreate):
    id: int
    date: datetime
    time: datetime
