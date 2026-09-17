from dataclasses import  dataclass
from typing import Literal

@dataclass
class RawUserData:
    uid: str
    cn: str
    pwd: None | str
    main_grp: None | int
    other_grp: None | str
    employment_status: Literal[1, 2]