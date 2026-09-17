"""原本給前端更新補位課程和今天課程 endpoint.

.. deprecated:: 2025.7.1
    已改為 WebSockets 溝通

.. todo:: 安全把這個刪掉
"""
import logging

from fastapi import APIRouter

from src.database.exec_sql import exec_sql

logger = logging.getLogger("rich")
from datetime import datetime

router = APIRouter(
    prefix="/status",
    tags=["Status"],
)


@router.get("/")
async def get_class_with_seats():
    # TODO
    """_summary_.

    Returns
    -------
    _type_
        _description_
    .. todo:: - 解決此處顯示的 Ruff 錯誤
        - 將此邏輯移至獨立的 service 檔案中
    *由 林家民 於 2025/7/23 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文。*
    """
    class_with_seats = await exec_sql("one", "single_get_remaining")
    if class_with_seats:

        class_with_seats["座位"] = [
            {"座位": seat, "號碼": seat_num}
            for seat, seat_num in zip(
                class_with_seats["座位"].split(","),
                class_with_seats["座位號"].split(","), strict=False,
            )
        ]

        class_with_seats["男座位"] = []
        class_with_seats["女座位"] = []
        for seat in class_with_seats["座位"]:
            if int(seat["座位"][-2:]) <= 15:
                class_with_seats["女座位"].append(seat)
            else:
                class_with_seats["男座位"].append(seat)

        del class_with_seats["座位"]
        del class_with_seats["座位號"]

    current_date = datetime.now().strftime("%Y/%m/%d")

    h = datetime.now().hour
    if 12 <= h <= 17:
        current_period = 2
    elif h <= 11:
        current_period = 1
    else:
        current_period = 3

    # current_date = '2023/08/15'  # DEBUG USE
    # current_period = 1  # DEBUG USE

    classes_today: list = await exec_sql(
        "all",
        "classes_today",
        current_date=current_date,
        current_period=current_period,
    )
    if len(classes_today) > 0:
        for c in classes_today:
            c["教室"] = [
                ,
                ,
                ,
                ,
                ,
            ][c["教室"] - 1]
    return {"class_with_seats": class_with_seats,
            "classes_today": classes_today}
