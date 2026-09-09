"""Pydantic models.

詳情見: https://docs.pydantic.dev/latest/ 以及 https://fastapi.tiangolo.com/tutorial/body-nested-models/

*由 林家民 於 2025/7/25 撰寫*
"""
from .announcement import AddAnnouncement, Announcement, UpdateAnnouncement  # noqa: F401
from .api_response import APIResponse  # noqa: F401
from .cardholder import Cardholder  # noqa: F401
from .device import Device  # noqa: F401
from .device_info import DeviceInfo  # noqa: F401
from .fetch_role import FetchRoleResponse  # noqa: F401
