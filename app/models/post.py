from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class PostStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class XPost(BaseModel):
    id: Optional[str] = None
    content: str
    scheduled_date: datetime
    timezone: str
    status: PostStatus = PostStatus.PENDING
    thread_id: Optional[str] = None
    thread_position: Optional[int] = None
    thread_title: Optional[str] = None
    media_urls: Optional[List[str]] = None
    x_post_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator("content")
    def validate_content_length(cls, v):
        if len(v) > 280:
            raise ValueError(f"Content exceeds 280 characters (currently {len(v)})")
        return v

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class XThread(BaseModel):
    id: str
    title: Optional[str] = None
    posts: List[XPost] = []
    scheduled_date: datetime
    timezone: str
    status: PostStatus = PostStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }
