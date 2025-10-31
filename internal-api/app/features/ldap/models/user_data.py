from dataclasses import dataclass


@dataclass
class UserData:
    uid: str
    employeenumber: str
    departmentnumber: str
    cn: str
    givenname: str
    sn: str
    pwd: str | None
    main_grp: str
    other_grp: list | None
    main_grp_id: str
    other_grp_ids: list | None
    mail: str
