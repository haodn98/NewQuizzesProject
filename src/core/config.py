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

    SECRET_KEY: str
    ALGORITHM: str
    access_token_expire_minutes: int = 3600

    PGADMIN_DEFAULT_EMAIL: str
    PGADMIN_DEFAULT_PASSWORD: str

    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_USER: str
    EMAIL_PASSWORD: str

    REDIS_URL: str

    MONGO_URL:str
    MONGO_DB:str
    MONGO_COLLECTION:str

    class Config:
        env_file = ".env"

settings = Settings()