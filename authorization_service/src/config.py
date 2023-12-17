from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    Apiantsiak: str

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env"),
        env_file_encoding='utf-8'
    )


settings = Settings()
