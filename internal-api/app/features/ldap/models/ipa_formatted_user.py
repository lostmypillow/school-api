from dataclasses import dataclass


@dataclass
class IpaFormattedUser:
    uid: str
    employeenumber: str
    departmentnumber: int
    cn: str
    givenname: str
    sn: str
    pwd: str | None
    main_grp: str
    main_grp_id: int
    other_grp: list | None
    other_grp_ids: list | None
    mail: str
