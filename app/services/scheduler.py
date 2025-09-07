import uuid
from datetime import datetime
from typing import Dict, List, Optional

import pytz
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from app.core.config import settings
from app.models.post import PostStatus, XPost, XThread
from app.services.x_api import XAPIService


class SchedulerService:
    def __init__(self):
        """Initialize the scheduler service."""
        self.x_api = XAPIService()
        self.scheduler = self._initialize_scheduler()
        self.posts: Dict[str, XPost] = {}
        self.threads: Dict[str, XThread] = {}
        self.monthly_post_count = 0
        self.max_monthly_posts = settings.MAX_MONTHLY_POSTS

    def _initialize_scheduler(self) -> BackgroundScheduler:
        """Initialize the APScheduler with appropriate configuration."""
        # Define job stores
        jobstores = {"default": MemoryJobStore()}

        # Define executors
        executors = {"default": ThreadPoolExecutor(20)}

        # Create and configure the scheduler
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone=pytz.timezone(settings.TZ),
        )

        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")

        return scheduler

    def schedule_post(self, post: XPost) -> bool:
        """
        Schedule a single post for publication.

        Args:
            post: The XPost object to schedule

        Returns:
            True if scheduled successfully, False otherwise
        """
        if self.monthly_post_count >= self.max_monthly_posts:
            logger.warning(f"Monthly post limit reached: {self.max_monthly_posts}")
            return False

        try:
            # Generate an ID if not provided
            if not post.id:
                post.id = str(uuid.uuid4())

            # Store the post
            self.posts[post.id] = post

            # Create a job to publish the post at the scheduled time
            self.scheduler.add_job(
                self._publish_post_job,
                "date",
                run_date=post.scheduled_date,
                args=[post.id],
                id=f"post_{post.id}",
                replace_existing=True,
            )

            # Update post status
            post.status = PostStatus.SCHEDULED
            self.monthly_post_count += 1

            logger.info(f"Scheduled post {post.id} for {post.scheduled_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule post {post.id}: {e}")
            return False

    def schedule_thread(self, thread: XThread) -> bool:
        """
        Schedule a thread for publication.

        Args:
            thread: The XThread object to schedule

        Returns:
            True if scheduled successfully, False otherwise
        """
        if not thread.posts or len(thread.posts) == 0:
            logger.warning(f"Thread {thread.id} has no posts to schedule")
            return False

        if self.monthly_post_count + len(thread.posts) > self.max_monthly_posts:
            logger.warning(
                f"Monthly post limit would be exceeded by thread {thread.id}"
            )
            return False

        try:
            # Store the thread
            self.threads[thread.id] = thread

            # Create a job to publish the thread at the scheduled time
            self.scheduler.add_job(
                self._publish_thread_job,
                "date",
                run_date=thread.scheduled_date,
                args=[thread.id],
                id=f"thread_{thread.id}",
                replace_existing=True,
            )

            # Update thread status
            thread.status = PostStatus.SCHEDULED
            self.monthly_post_count += len(thread.posts)

            logger.info(
                f"Scheduled thread {thread.id} with {len(thread.posts)} posts for {thread.scheduled_date}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to schedule thread {thread.id}: {e}")
            return False

    def _publish_post_job(self, post_id: str) -> None:
        """
        Job function to publish a post. Called by the scheduler.

        Args:
            post_id: The ID of the post to publish
        """
        try:
            post = self.posts.get(post_id)
            if not post:
                logger.error(f"Post {post_id} not found")
                return

            # Attempt to publish the post
            x_post_id = self.x_api.publish_post(post)

            if x_post_id:
                post.x_post_id = x_post_id
                post.status = PostStatus.PUBLISHED
                logger.info(
                    f"Successfully published post {post_id} to X with ID {x_post_id}"
                )
            else:
                post.status = PostStatus.FAILED
                logger.error(f"Failed to publish post {post_id}")

        except Exception as e:
            logger.error(f"Error in publish post job for {post_id}: {e}")
            if post_id in self.posts:
                self.posts[post_id].status = PostStatus.FAILED

    def _publish_thread_job(self, thread_id: str) -> None:
        """
        Job function to publish a thread. Called by the scheduler.

        Args:
            thread_id: The ID of the thread to publish
        """
        try:
            thread = self.threads.get(thread_id)
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return

            # Attempt to publish the thread
            success = self.x_api.publish_thread(thread)

            if success:
                thread.status = PostStatus.PUBLISHED
                logger.info(f"Successfully published thread {thread_id} to X")
            else:
                thread.status = PostStatus.FAILED
                logger.error(f"Failed to publish thread {thread_id}")

        except Exception as e:
            logger.error(f"Error in publish thread job for {thread_id}: {e}")
            if thread_id in self.threads:
                self.threads[thread_id].status = PostStatus.FAILED

    def get_scheduled_posts(self) -> List[XPost]:
        """Get all scheduled individual posts."""
        return list(self.posts.values())

    def get_scheduled_threads(self) -> List[XThread]:
        """Get all scheduled threads."""
        return list(self.threads.values())

    def get_post(self, post_id: str) -> Optional[XPost]:
        """Get a specific post by ID."""
        return self.posts.get(post_id)

    def get_thread(self, thread_id: str) -> Optional[XThread]:
        """Get a specific thread by ID."""
        return self.threads.get(thread_id)

    def cancel_post(self, post_id: str) -> bool:
        """
        Cancel a scheduled post.

        Args:
            post_id: The ID of the post to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        if post_id not in self.posts:
            return False

        try:
            # Remove the job from the scheduler
            self.scheduler.remove_job(f"post_{post_id}")

            # Update post status
            post = self.posts[post_id]
            post.status = PostStatus.CANCELLED
            self.monthly_post_count -= 1

            logger.info(f"Cancelled post {post_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel post {post_id}: {e}")
            return False

    def cancel_thread(self, thread_id: str) -> bool:
        """
        Cancel a scheduled thread.

        Args:
            thread_id: The ID of the thread to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        if thread_id not in self.threads:
            return False

        try:
            # Remove the job from the scheduler
            self.scheduler.remove_job(f"thread_{thread_id}")

            # Update thread status
            thread = self.threads[thread_id]
            thread.status = PostStatus.CANCELLED
            self.monthly_post_count -= len(thread.posts)

            logger.info(f"Cancelled thread {thread_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel thread {thread_id}: {e}")
            return False

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")
