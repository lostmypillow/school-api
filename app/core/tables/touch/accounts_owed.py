from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.tables.base import Base


class AccountsOwed(Base):
    __tablename__ = "accounts_owed"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    legacy_course_num_2: Mapped[str] = mapped_column(String(20), primary_key=True)
    owes_money: Mapped[Optional[Decimal]] = mapped_column(Numeric[Decimal](precision=12, scale=2))
    owed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric[Decimal](precision=12, scale=2))
