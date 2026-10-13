"""可重複使用的函式與依賴項.

與其他資料夾不同, 目前我尚未規劃這部分的重構 todo, 因為在撰寫此說明時, `` refactor branch 中尚未有對應實作. 有想過把 `src.lib.get_class_with_seats` 轉為 services, *但* 重構這部分並非必要.


"""  # noqa: E501

from .deps import deps
from .get_class_with_seats import get_class_with_seats
