from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.core.config import settings
from app.models.post import PostStatus
from app.services.instance import scheduler_instance as scheduler

router = APIRouter()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard view showing scheduled posts and threads."""
    posts = scheduler.get_scheduled_posts()
    threads = scheduler.get_scheduled_threads()

    # Calculate statistics
    stats = {
        "scheduled": len(posts) + sum(len(thread.posts) for thread in threads),
        "published": sum(1 for post in posts if post.status == PostStatus.PUBLISHED)
        + sum(1 for thread in threads if thread.status == PostStatus.PUBLISHED),
        "failed": sum(1 for post in posts if post.status == PostStatus.FAILED)
        + sum(1 for thread in threads if thread.status == PostStatus.FAILED),
        "percent_used": (
            int((scheduler.monthly_post_count / settings.MAX_MONTHLY_POSTS) * 100)
            if settings.MAX_MONTHLY_POSTS > 0
            else 0
        ),
    }

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "title": "Dashboard",
            "request": request,
            "posts": posts,
            "threads": threads,
            "stats": stats,
        },
    )


@router.get("/post/{post_id}", response_class=HTMLResponse)
def post_detail(request: Request, post_id: str):
    """View showing details for a specific post."""
    post = scheduler.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        "pages/post_detail.html",
        {"title": "Post Detail", "request": request, "post": post},
    )


@router.get("/thread/{thread_id}", response_class=HTMLResponse)
def thread_detail(request: Request, thread_id: str):
    """View showing details for a specific thread."""
    thread = scheduler.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return templates.TemplateResponse(
        "pages/thread_detail.html",
        {"title": "Thread Detail", "request": request, "thread": thread},
    )


@router.get("/cancel-post/{post_id}", response_class=HTMLResponse)
def cancel_post(request: Request, post_id: str):
    """Cancel a scheduled post and redirect to dashboard."""
    success = scheduler.cancel_post(post_id)
    if not success:
        logger.error(f"Failed to cancel post {post_id}")

    return dashboard(request)


@router.get("/cancel-thread/{thread_id}", response_class=HTMLResponse)
def cancel_thread(request: Request, thread_id: str):
    """Cancel a scheduled thread and redirect to dashboard."""
    success = scheduler.cancel_thread(thread_id)
    if not success:
        logger.error(f"Failed to cancel thread {thread_id}")

    return dashboard(request)
