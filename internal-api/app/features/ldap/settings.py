from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    IPA_CA: str =  str(Path(__file__).resolve().parent / "data" / "ipa-ca.crt")
    IPA_HOST: str = "https://ldap."
    IPA_ADMIN_PASS: str =""
    IPA_USER: str = "admin"
    DRY_RUN: bool = False


settings = Settings()
