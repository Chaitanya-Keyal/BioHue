from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = Field(..., env="MONGO_URI")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    database_name: str = Field("biohue", env="DATABASE_NAME")

    class Config:
        env_file = ".env"


settings = Settings()
