from typing import Literal
from sqlalchemy import String, Integer, SmallInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VMDetails(Base):
    __tablename__ = "vm_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    vm_name: Mapped[str] = mapped_column(String, primary_key=False)

    human_owner: Mapped[str | None] = mapped_column(String, nullable=True)
    pc_owner: Mapped[str | None] = mapped_column(String, nullable=True)

    # Store Literal[0, 1] flags as SmallInteger
    pve: Mapped[Literal[0, 1]] = mapped_column(SmallInteger, nullable=False)

    pve_host: Mapped[str | None] = mapped_column(String, default=None, nullable=True)
    pve_token_username: Mapped[str | None] = mapped_column(
        String, default=None, nullable=True
    )
    pve_token_name: Mapped[str | None] = mapped_column(
        String, default=None, nullable=True
    )
    pve_token_value: Mapped[str | None] = mapped_column(
        String, default=None, nullable=True
    )
    pve_vm_id: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True)

    proxy_from: Mapped[str | None] = mapped_column(String, default=None, nullable=True)
    pve_proxy: Mapped[str | None] = mapped_column(String, default=None, nullable=True)
    spice_proxy: Mapped[str] = mapped_column(String, nullable=False)
    vm_password: Mapped[str | None] = mapped_column(String, default=None, nullable=True)

    usb: Mapped[Literal[0, 1]] = mapped_column(SmallInteger, nullable=False)
