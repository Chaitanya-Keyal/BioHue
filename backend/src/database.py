from datetime import datetime
from typing import Optional

import pytz
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic import BaseModel, Field
from src.config import settings as config

client = AsyncIOMotorClient(config.mongo_uri)
db = client[config.database_name]


fs = AsyncIOMotorGridFSBucket(db)

users_collection = db["users"]
sessions_collection = db["sessions"]
images_collection = db["images"]


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=pytz.timezone("Asia/Kolkata"))
    )


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    username: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=pytz.timezone("Asia/Kolkata"))
    )


class Analysis(BaseModel):
    metric: str
    substrate: str
    value: float
    result: str


class File(BaseModel):
    id: str = Field(..., alias="_id")
    base64: Optional[str] = None


class Image(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str
    md5_hash: str
    original_image: File
    processed_image: Optional[File] = None
    analysis: Optional[Analysis] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=pytz.timezone("Asia/Kolkata"))
    )
