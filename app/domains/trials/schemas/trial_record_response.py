from datetime import datetime

from app.domains.trials.schemas.trial_record_base import TrialRecordBase


class TrialRecordResponse(TrialRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime
