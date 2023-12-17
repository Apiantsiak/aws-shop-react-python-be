from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    UPLOAD_BUCKET: str
    UPLOAD_FOLDER: str
    PARSED_FOLDER: str
    EXPIRATION_SECONDS: int
    SQS_UPLOAD_ARN: str
    UPLOAD_QUEUE_NAME: str
    BASIC_AUTH_LAMBDA_ARN: str

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env"),
        env_file_encoding='utf-8'
    )


settings = Settings()
