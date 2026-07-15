from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    # ------ LLMs ------
    OPENAI_API_KEY: str

    # ------ File control ------
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int  #KB

    # ------- Vector Store -------
    MONGO_URI:str
    MONGO_DATABASE_NAME:str


    class Config:
        env_file = ".env"

def get_settings() -> Setting:
    return Setting()