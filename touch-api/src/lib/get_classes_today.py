from typing import Any, Union
from src.database.exec_sql import exec_sql
from datetime import datetime
import os


async def get_classes_today() -> list[dict[str, Union[str, int]]]:
    if os.getenv('DEBUG') == 'True':
        return [
            {
                "教室": ,
                "內容": "",
                "時間": "09:00",
                "": 1
            },
            {
                "教室": ,
                "內容": "",
                "時間": "09:00",
                "": 1
            }
        ]

    current_date = datetime.now().strftime('%Y/%m/%d')

    h = datetime.now().hour
    if 12 <= h <= 17:
        current_period = 2
    elif h <= 11:
        current_period = 1
    else:
        current_period = 3

    # current_date = '2023/08/15'  # DEBUG USE
    # current_period = 1  # DEBUG USE


    classes_today: list[dict[str, Union[str, int]]] = await exec_sql(
        'all',
        'classes_today',
        current_date=current_date,
        current_period=current_period
    )
    if classes_today != []:
        for c in classes_today:
            c['教室'] = [
                ,
                ,
                ,
                ,
                
            ][c['教室'] - 1]
    return classes_today
