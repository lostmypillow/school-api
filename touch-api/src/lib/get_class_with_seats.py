from typing import Union
from src.database.async_operations import exec_sql
import os


async def get_class_with_seats() -> dict[str, Union[str, list[str]]]:

    class_with_seats: dict[str, Union[str, list[str]]] = await exec_sql('one', 'single_get_remaining')
    if class_with_seats == {}:
        return class_with_seats

    # convert 位子, which is a string with a lot of commas, into a list
    # SQ.座位號,
    # SQ.座位
    class_with_seats['座位'] = [
        {"座位": seat, "號碼": seat_num}
        for seat, seat_num in zip(
            class_with_seats['座位'].split(','),
            class_with_seats['座位號'].split(',')
        )
    ]

    class_with_seats['男座位'] = []
    class_with_seats['女座位'] = []
    for seat in class_with_seats['座位']:
        if int(seat["座位"][-2:]) <= 15:
            class_with_seats['女座位'].append(seat)
        else:
            class_with_seats['男座位'].append(seat)

    del class_with_seats['座位']
    del class_with_seats['座位號']

    return class_with_seats
