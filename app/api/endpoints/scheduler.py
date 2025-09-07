from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.services.instance import scheduler_instance as scheduler

router = APIRouter()


@router.get("/posts")
def get_scheduled_posts():
    """Get all scheduled posts."""
    return scheduler.get_scheduled_posts()


@router.get("/threads")
def get_scheduled_threads():
    """Get all scheduled threads."""
    return scheduler.get_scheduled_threads()


@router.get("/post/{post_id}")
def get_post(post_id: str):
    """Get a specific post by ID."""
    post = scheduler.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/thread/{thread_id}")
def get_thread(thread_id: str):
    """Get a specific thread by ID."""
    thread = scheduler.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.post("/cancel-post/{post_id}")
def cancel_post(post_id: str):
    """Cancel a scheduled post."""
    success = scheduler.cancel_post(post_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Post not found or could not be cancelled"
        )
    logger.info(f"Post {post_id} cancelled")
    return {"success": True, "message": f"Post {post_id} cancelled"}


@router.post("/cancel-thread/{thread_id}")
def cancel_thread(thread_id: str):
    """Cancel a scheduled thread."""
    success = scheduler.cancel_thread(thread_id)
    if not success:
        raise HTTPException(
            status_code=404, detail="Thread not found or could not be cancelled"
        )
    logger.info(f"Thread {thread_id} cancelled")
    return {"success": True, "message": f"Thread {thread_id} cancelled"}
