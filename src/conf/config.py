from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    sqlalchemy_database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/todo_db"
    secret_key: str = "secret key"
    algorithm: str = "HS256"
    mail_username: str = "example@meta.ua"
    mail_password: str = "qwerty"
    mail_from: str = "example@meta.ua"
    mail_from_name: str = "test"
    mail_port: int =465
    mail_server: str = "smtp.meta.ua"
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = 'password'
    redis_db: str = 'database'
    cloudinary_name: str = "cloudinary_name"
    cloudinary_api_key: str = "123"
    cloudinary_api_secret: str = "213213"
    openai_api_key: str = "213213"

    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"


settings = Settings()

class Config:
    DB_URL = settings.sqlalchemy_database_url


class RedisConfig:
    host = settings.redis_host
    port = settings.redis_port
    password = settings.redis_password
    db = settings.redis_db


config = Config
redis_config = RedisConfig
