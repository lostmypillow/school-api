from pydantic import BaseModel
class IpaFormattedUser(BaseModel):
    uid: str
    employeenumber: str
    departmentnumber: int
    cn: str
    givenname: str
    sn: str
    pwd: str | None
    main_grp: str
    main_grp_id: int
    other_grp: list
    other_grp_ids: list | None
    mail: str
