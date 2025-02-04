from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    SMB_HOST: str = ""
    SMB_FOLDER: str = "\\\\"
    SMB_USERNAME: str = 
    SMB_PASSWORD: str = 
    # SMB_SERVER=
    # SMB_FOLDER=
    # SMB_USERNAME=
    # SMB_PASSWORD=
    DEBUG: bool = True
# TODO replace debug values
settings = Settings()
