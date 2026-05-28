from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    db_name : str = "enterprise_data"
    db_user: str = "postgres"
    db_pass: str = Field("postgres", validation_alias=AliasChoices("db_pass", "db_password"))
    db_host: str = "127.0.0.1" 
    db_port: int = 5432

    exchange_rate_api_key: str 
    
    model_config = SettingsConfigDict(
        env_file = str(BASE_DIR / ".env"),
        env_file_encoding = "utf-8",
        extra = "ignore"
    )

settings = Settings()
