import json
import os
from typing import Dict

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Thresholds(BaseModel):
    negative: str = Field(..., description="Condition for negative classification")
    positive: str = Field(..., description="Condition for positive classification")


class SubstrateConfig(BaseModel):
    metric: str = Field(..., description="Metric name to be displayed")
    expression: str = Field(..., description="Mathematical expression using r, g, b")
    thresholds: Thresholds


class Settings(BaseSettings):
    ENV: str = Field(..., env="ENV")
    LOCAL_ENV: str = "LOCAL"
    PROD_ENV: str = "PROD"

    mongo_uri: str = Field(..., env="MONGO_URI")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    database_name: str = Field("biohue", env="DATABASE_NAME")
    substrates: Dict[str, SubstrateConfig]

    class Config:
        env_file = ".env"


def load_substrate_config(file_path: str) -> Dict[str, SubstrateConfig]:
    with open(file_path, "r") as f:
        data: dict = json.load(f)
    return {k: SubstrateConfig(**v) for k, v in data.items()}


settings = Settings(
    substrates=load_substrate_config(
        os.path.join(os.path.dirname(__file__), "substrates.json")
    )
)
