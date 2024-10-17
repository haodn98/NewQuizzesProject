import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Quizzes Project"
    debug: bool = False
    version: str = "1.0.0"

    DB_NAME:str
    DB_USER:str
    DB_PASS:str
    DB_HOST:str
    DB_PORT:str

    TEST_DB_NAME:str
    TEST_DB_USER:str
    TEST_DB_PASS:str
    TEST_DB_HOST:str
    TEST_DB_PORT:str

    SECRET_KEY: str
    ALGORITHM: str
    access_token_expire_minutes: int = 3600

    PGADMIN_DEFAULT_EMAIL: str
    PGADMIN_DEFAULT_PASSWORD: str

    REDIS_URL: str

    MONGO_URL:str
    MONGO_DB:str
    MONGO_COLLECTION:str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    CELERY_TIMEZONE: str = 'UTC'

    model_config = ConfigDict(
        env_file=".env-non-dev" if os.getenv("DOCKER_ENV") else ".env",
        extra="ignore"
    )

settings = Settings()