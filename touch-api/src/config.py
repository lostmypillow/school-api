from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = ""
    DB_USERNAME: str = 
    DB_PASSWORD: str = 
#    DB_HOST: str = ""
#    DB_USERNAME: str = ""
#    DB_PASSWORD: str = ""
    DB_NAME: str = ""
    SMB_HOST: str = ""
    SMB_FOLDER: str = "\\\\"
    SMB_USERNAME: str = 
    SMB_PASSWORD: str = 
    DEBUG: bool = True


# TODO replace debug values
settings = Settings()
