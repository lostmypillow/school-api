from pydantic import BaseModel, computed_field
from app.features.ldap.models.ipa_formatted_user import IpaFormattedUser


class FilteredList(BaseModel):
    # List of users uid to disable and/or make sure it's disabled
    users_to_disable: list[str]
    users_to_add: list[IpaFormattedUser]


class FilteredResponse(FilteredList):
    @computed_field
    @property
    def num_to_disable(self) -> int:
        return len(self.to_disable)

    @computed_field
    @property
    def num_to_add(self) -> int:
        return len(self.to_add)
