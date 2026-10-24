import os
from anyio import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    IPA_CA: str =  str(Path(__file__).parent / "data" / "ipa-ca.crt")
    # These fields will be populated by IPA_HOST, IPA_ADMIN_PASS, etc.
    IPA_HOST: str = os.getenv("IPA_HOST", "")
    IPA_ADMIN_PASS: str = os.getenv("IPA_ADMIN_PASS", "")
    IPA_USER: str = "admin"
    DRY_RUN: bool = False

    model_config = SettingsConfigDict(env_file=None)


settings = Settings()

