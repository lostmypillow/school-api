from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USERNAME: str = "testsql"
    DB_PASSWORD: str = "test123456"
    DB_HOST: str = "192.168.2.8"
    DB_NAME: str = ""
#   DB_USERNAME: str = "mssql"
#   DB_PASSWORD: str = "mssql"
#   DB_HOST: str = "192.168.2.12"


settings = Settings()
