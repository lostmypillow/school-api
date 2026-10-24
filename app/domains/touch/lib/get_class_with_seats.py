from datetime import datetime

from app.core.exec_mssql_async import exec_mssql_async


async def get_class_with_seats() -> dict:
    class_with_seats_result = await exec_mssql_async("single_get_remaining")
    class_with_seats = class_with_seats_result[0]
    if class_with_seats:

        class_with_seats["座位"] = [
            {"座位": seat, "號碼": seat_num}
            for seat, seat_num in zip(
                class_with_seats["座位"].split(","),
                class_with_seats["seat_no"].split(","), strict=False,
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
        del class_with_seats["seat_no"]

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

    classes_today: list = await exec_mssql_async(
        "classes_today",
        current_date,
        current_period,
    )
    return {
        "class_with_seats": class_with_seats,
        "classes_today": classes_today,
    }
