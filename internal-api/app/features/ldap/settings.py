from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    IPA_CA: str = ""
    IPA_HOST: str = ""
    IPA_PASS: str = ""
    IPA_USER: str = ""


settings = Settings()
