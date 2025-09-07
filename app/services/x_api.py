import os
import time
from typing import List, Optional

import tweepy
from loguru import logger

from app.core.config import settings
from app.models.post import PostStatus, XPost, XThread


class XAPIService:
    def __init__(self):
        """Initialize the X API service with credentials from settings."""
        self.client = self._initialize_client()

    def _initialize_client(self) -> tweepy.Client:
        """Initialize the tweepy client with OAuth 1.0a User Context authentication."""
        try:
            client = tweepy.Client(
                consumer_key=settings.X_CONSUMER_KEY,
                consumer_secret=settings.X_CONSUMER_SECRET,
                access_token=settings.X_ACCESS_TOKEN,
                access_token_secret=settings.X_ACCESS_TOKEN_SECRET,
            )
            return client
        except Exception as e:
            logger.error(f"Failed to initialize X API client: {e}")
            raise

    def publish_post(self, post: XPost) -> Optional[str]:
        """
        Publish a single post to X.

        Args:
            post: The XPost object to publish

        Returns:
            The X post ID if successful, None otherwise
        """
        try:
            # Handle media if present
            media_ids = []
            if post.media_urls and len(post.media_urls) > 0:
                auth = tweepy.OAuth1UserHandler(
                    settings.X_CONSUMER_KEY,
                    settings.X_CONSUMER_SECRET,
                    settings.X_ACCESS_TOKEN,
                    settings.X_ACCESS_TOKEN_SECRET,
                )
                api = tweepy.API(auth)

                for media_url in post.media_urls:
                    # Download media to a temporary file
                    if media_url.startswith(("http://", "https://")):
                        import tempfile

                        import requests

                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        try:
                            r = requests.get(media_url, stream=True)
                            r.raise_for_status()
                            with open(temp_file.name, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)

                            # Upload media
                            media = api.media_upload(temp_file.name)
                            media_ids.append(media.media_id)
                        finally:
                            temp_file.close()
                            if os.path.exists(temp_file.name):
                                os.unlink(temp_file.name)
                    else:
                        # Local file
                        if os.path.exists(media_url):
                            media = api.media_upload(media_url)
                            media_ids.append(media.media_id)

            # Post the tweet
            response = self.client.create_tweet(
                text=post.content, media_ids=media_ids if media_ids else None
            )

            if response and hasattr(response, "data") and "id" in response.data:
                post_id = response.data["id"]
                logger.info(f"Successfully published post: {post_id}")
                return post_id
            else:
                logger.error(f"Failed to publish post, unexpected response: {response}")
                return None

        except Exception as e:
            logger.error(f"Failed to publish post: {e}")
            return None

    def publish_thread(self, thread: XThread) -> bool:
        """
        Publish a thread to X.

        Args:
            thread: The XThread object containing posts to publish as a thread

        Returns:
            True if successful, False otherwise
        """
        if not thread.posts or len(thread.posts) == 0:
            logger.warning(f"Thread {thread.id} has no posts to publish")
            return False

        try:
            # Sort posts by position
            posts = sorted(thread.posts, key=lambda p: p.thread_position or 0)

            # Publish the first post
            first_post = posts[0]
            first_post_id = self.publish_post(first_post)

            if not first_post_id:
                logger.error(f"Failed to publish first post of thread {thread.id}")
                return False

            # Update the first post with its X ID
            first_post.x_post_id = first_post_id
            first_post.status = PostStatus.PUBLISHED

            # Publish remaining posts as replies
            prev_post_id = first_post_id
            for post in posts[1:]:
                # Add small delay between posts to avoid rate limits
                time.sleep(2)

                try:
                    # Handle media if present
                    media_ids = []
                    if post.media_urls and len(post.media_urls) > 0:
                        auth = tweepy.OAuth1UserHandler(
                            settings.X_CONSUMER_KEY,
                            settings.X_CONSUMER_SECRET,
                            settings.X_ACCESS_TOKEN,
                            settings.X_ACCESS_TOKEN_SECRET,
                        )
                        api = tweepy.API(auth)

                        for media_url in post.media_urls:
                            # Handle media uploading (similar to publish_post)
                            if media_url.startswith(("http://", "https://")):
                                import tempfile

                                import requests

                                temp_file = tempfile.NamedTemporaryFile(delete=False)
                                try:
                                    r = requests.get(media_url, stream=True)
                                    r.raise_for_status()
                                    with open(temp_file.name, "wb") as f:
                                        for chunk in r.iter_content(chunk_size=8192):
                                            f.write(chunk)

                                    # Upload media
                                    media = api.media_upload(temp_file.name)
                                    media_ids.append(media.media_id)
                                finally:
                                    temp_file.close()
                                    if os.path.exists(temp_file.name):
                                        os.unlink(temp_file.name)
                            else:
                                # Local file
                                if os.path.exists(media_url):
                                    media = api.media_upload(media_url)
                                    media_ids.append(media.media_id)

                    # Post the reply
                    response = self.client.create_tweet(
                        text=post.content,
                        media_ids=media_ids if media_ids else None,
                        in_reply_to_tweet_id=prev_post_id,
                    )

                    if response and hasattr(response, "data") and "id" in response.data:
                        post_id = response.data["id"]
                        post.x_post_id = post_id
                        post.status = PostStatus.PUBLISHED
                        prev_post_id = post_id
                        logger.info(f"Successfully published thread post: {post_id}")
                    else:
                        logger.error(
                            f"Failed to publish thread post, unexpected response: {response}"
                        )
                        return False

                except Exception as e:
                    logger.error(f"Failed to publish thread post: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to publish thread: {e}")
            return False
