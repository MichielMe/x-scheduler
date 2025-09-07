import csv
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytz
from loguru import logger

from app.models.post import XPost, XThread


class CSVProcessor:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

    def process_csv(self) -> Tuple[List[XPost], Dict[str, XThread]]:
        """
        Process the CSV file and create XPost and XThread objects.

        Returns:
            Tuple containing a list of individual posts and a dictionary of threads
        """
        if not self.csv_path.exists():
            logger.error(f"CSV file not found: {self.csv_path}")
            return [], {}

        posts = []
        threads: Dict[str, XThread] = {}

        try:
            with open(self.csv_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    post = self._create_post_from_row(row)

                    # Process as part of a thread if thread_id exists
                    if post.thread_id:
                        if post.thread_id not in threads:
                            threads[post.thread_id] = XThread(
                                id=post.thread_id,
                                title=post.thread_title,
                                scheduled_date=post.scheduled_date,
                                timezone=post.timezone,
                                posts=[],
                            )
                        threads[post.thread_id].posts.append(post)
                    else:
                        posts.append(post)

            # Sort thread posts by position
            for thread_id, thread in threads.items():
                thread.posts.sort(key=lambda p: p.thread_position or 0)

            return posts, threads

        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            return [], {}

    def _create_post_from_row(self, row: Dict[str, str]) -> XPost:
        """Create an XPost object from a CSV row."""
        # Parse date and time
        date_str = row.get("date", "")
        time_str = row.get("time", "")
        timezone_str = row.get("timezone", "UTC")

        # Create datetime object
        dt_str = f"{date_str} {time_str}"
        try:
            # Try with seconds format first
            scheduled_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Fall back to format without seconds
            scheduled_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        # Handle timezone
        timezone = pytz.timezone(timezone_str)
        scheduled_date = (
            timezone.localize(scheduled_date)
            if scheduled_date.tzinfo is None
            else scheduled_date
        )

        # Parse media URLs if present
        media_urls = None
        if row.get("media_urls"):
            media_urls = [
                url.strip()
                for url in row.get("media_urls", "").split(",")
                if url.strip()
            ]

        # Create XPost object
        return XPost(
            id=str(uuid.uuid4()),
            content=row.get("content", ""),
            scheduled_date=scheduled_date,
            timezone=timezone_str,
            thread_id=row.get("thread_id") if row.get("thread_id") else None,
            thread_position=(
                int(row.get("thread_position", 0))
                if row.get("thread_position")
                else None
            ),
            thread_title=row.get("thread_title") if row.get("thread_title") else None,
            media_urls=media_urls,
        )
