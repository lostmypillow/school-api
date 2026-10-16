from pydantic import BaseModel, computed_field
from app.domains.ldap.schemas.ipa_formatted_user import IpaFormattedUser


class FilteredList(BaseModel):
    # List of employees uid to disable and/or make sure it's disabled
    employees_to_disable: list[IpaFormattedUser]
    employees_to_add: list[IpaFormattedUser]

    @computed_field
    @property
    def num_to_disable(self) -> int:
        return len(self.employees_to_disable)

    @computed_field
    @property
    def num_to_add(self) -> int:
        return len(self.employees_to_add)
