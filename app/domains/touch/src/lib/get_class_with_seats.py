"""取得班級資訊, 包括補位座位(男 + 女)、目前補位班級與即將上課的課程資訊.


"""
from datetime import datetime

from src.database.exec_sql import exec_sql


async def get_class_with_seats() -> dict:
    """取得補位座位資訊與今日課表.

    Returns
    -------
    dict
    {
    "class_with_seats": class_with_seats,
    "classes_today": classes_today,
    }

    .. attention:: 註解區塊
    有兩段被註解掉的程式區塊標記為 'DEBUG USE', 因為測試資料庫中沒有任何 "classes_today"。如果你想強制讓前端出現資料, 這些就是你要解除註解的值, 以便讓 "classes_today" 的 SQL 查詢有輸出。

    .. todo::
        從 `if class_with_seats` 開始的邏輯……能否整合進 `src/database/sql/single_get_remaining.sql` 的 SQL 裡?

    
    """  # noqa: E501
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
    if 11 <= h <= 16:
        current_period = 2
    elif h <= 10:
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
    return {
        "class_with_seats": class_with_seats,
        "classes_today": classes_today,
    }
