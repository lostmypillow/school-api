from typing import Union
from app.database.async_operations import exec_sql
async def get_class_with_seats() -> dict[str, Union[str, list[str]]]:
    class_with_seats: dict[str, Union[str, list[str]]] = await exec_sql('one', 'single_get_remaining')

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


# {
#   "主檔號": 4,
#   "班級名稱": "",
#   "班別": "",
#   "男座位": [
#     {
#       "座位": "A22",
#       "號碼": "55170"
#     },
#     {
#       "座位": "B21",
#       "號碼": "55171"
#     },
#     {
#       "座位": "B23",
#       "號碼": "55172"
#     },
#     {
#       "座位": "B18",
#       "號碼": "55173"
#     },
#     {
#       "座位": "D22",
#       "號碼": "55174"
#     },
#     {
#       "座位": "E22",
#       "號碼": "55175"
#     },
#     {
#       "座位": "F18",
#       "號碼": "55176"
#     },
#     {
#       "座位": "F23",
#       "號碼": "55177"
#     },
#     {
#       "座位": "H17",
#       "號碼": "55178"
#     },
#     {
#       "座位": "H21",
#       "號碼": "55179"
#     },
#     {
#       "座位": "I20",
#       "號碼": "55180"
#     },
#     {
#       "座位": "I22",
#       "號碼": "55181"
#     },
#     {
#       "座位": "J18",
#       "號碼": "55182"
#     },
#     {
#       "座位": "J22",
#       "號碼": "55183"
#     }
#   ],
#   "女座位": [
#     {
#       "座位": "A09",
#       "號碼": "55154"
#     },
#     {
#       "座位": "A13",
#       "號碼": "55155"
#     },
#     {
#       "座位": "A15",
#       "號碼": "55156"
#     },
#     {
#       "座位": "B08",
#       "號碼": "55157"
#     },
#     {
#       "座位": "B11",
#       "號碼": "55158"
#     },
#     {
#       "座位": "B15",
#       "號碼": "55159"
#     },
#     {
#       "座位": "C11",
#       "號碼": "55160"
#     },
#     {
#       "座位": "D10",
#       "號碼": "55161"
#     },
#     {
#       "座位": "E09",
#       "號碼": "55162"
#     },
#     {
#       "座位": "E11",
#       "號碼": "55163"
#     },
#     {
#       "座位": "G09",
#       "號碼": "55164"
#     },
#     {
#       "座位": "G14",
#       "號碼": "55165"
#     },
#     {
#       "座位": "H10",
#       "號碼": "55166"
#     },
#     {
#       "座位": "I15",
#       "號碼": "55167"
#     },
#     {
#       "座位": "I13",
#       "號碼": "55168"
#     }
#   ]
# }