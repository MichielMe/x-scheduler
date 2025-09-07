from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response model for CSV uploads."""

    success: bool
    message: str
    posts_scheduled: int = 0
    threads_scheduled: int = 0
