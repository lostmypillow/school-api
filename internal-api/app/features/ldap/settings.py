from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import Field


class Settings(BaseSettings):
    IPA_CA: str =  str(Path(__file__).resolve().parent / "data" / "ipa-ca.crt")
    # These fields will be populated by IPA_HOST, IPA_ADMIN_PASS, etc.
    IPA_HOST: str = Field(...)
    IPA_ADMIN_PASS: str = Field(...)
    IPA_USER: str = Field(...)
    DRY_RUN: bool = False

    model_config = SettingsConfigDict(env_file=None)


settings = Settings()

