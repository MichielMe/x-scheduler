import os
import shutil
import uuid
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import Dict

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import RedirectResponse
from loguru import logger

from app.core.config import settings
from app.schemas.upload import UploadResponse
from app.services.csv_processor import CSVProcessor
from app.services.instance import scheduler_instance as scheduler

router = APIRouter()


@router.post("/upload-csv", response_model=UploadResponse)
async def upload_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    csv_file: UploadFile = File(...),
):
    """
    Upload a CSV file containing post data for scheduling.

    The CSV should be in the format:
    content,date,time,timezone,thread_id,thread_position,thread_title,media_urls
    """
    try:
        # Validate file is a CSV
        if not csv_file.filename.endswith(".csv"):
            logger.error(f"Invalid file type uploaded: {csv_file.filename}")
            return RedirectResponse(
                url="/dashboard?error=Invalid file type. Please upload a CSV file.",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # Create directory if it doesn't exist
        upload_dir = Path(settings.CSV_PATH)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{csv_file.filename}"
        file_path = upload_dir / unique_filename

        # Save uploaded file
        try:
            contents = await csv_file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error(f"Failed to save CSV file: {e}")
            return RedirectResponse(
                url="/dashboard?error=Failed to save CSV file.",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # Process the CSV file in the background
        background_tasks.add_task(process_csv_file, str(file_path))

        return RedirectResponse(
            url="/dashboard?success=CSV file uploaded and being processed.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except Exception as e:
        logger.error(f"Error during CSV upload: {e}")
        return RedirectResponse(
            url=f"/dashboard?error=Upload failed: {str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


def process_csv_file(file_path: str) -> Dict:
    """Process the uploaded CSV file and schedule posts."""
    try:
        # Process the CSV file
        processor = CSVProcessor(file_path)
        posts, threads = processor.process_csv()

        # Count successfully scheduled items
        posts_scheduled = 0
        threads_scheduled = 0

        # Schedule individual posts
        for post in posts:
            if scheduler.schedule_post(post):
                posts_scheduled += 1

        # Schedule threads
        for thread_id, thread in threads.items():
            if scheduler.schedule_thread(thread):
                threads_scheduled += 1

        logger.info(
            f"CSV processing complete. Scheduled {posts_scheduled} posts and {threads_scheduled} threads"
        )
        return {
            "success": True,
            "message": f"Scheduled {posts_scheduled} posts and {threads_scheduled} threads",
            "posts_scheduled": posts_scheduled,
            "threads_scheduled": threads_scheduled,
        }

    except Exception as e:
        logger.error(f"Failed to process CSV file: {e}")
        return {
            "success": False,
            "message": f"Failed to process CSV: {str(e)}",
            "posts_scheduled": 0,
            "threads_scheduled": 0,
        }
    finally:
        # Clean up the file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to remove temporary CSV file: {e}")
