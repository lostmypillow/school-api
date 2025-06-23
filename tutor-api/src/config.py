from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "192.168.x.x"
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_NAME: str = ""


settings = Settings()
