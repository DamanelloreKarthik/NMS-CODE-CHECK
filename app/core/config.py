from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(...)

    class Config:
        env_file = ".env"

settings = Settings()
