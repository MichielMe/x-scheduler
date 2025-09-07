from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Project"
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: list[str] = []

    FRONTEND_DIR: Path = Path(__file__).parent.parent.parent / "frontend"
    TEMPLATES_DIR: Path = FRONTEND_DIR / "templates"
    STATIC_DIR: Path = FRONTEND_DIR / "static"

    X_CONSUMER_KEY: str
    X_CONSUMER_SECRET: str
    X_ACCESS_TOKEN: str
    X_ACCESS_TOKEN_SECRET: str
    X_CLIENT_ID: str
    X_CLIENT_SECRET: str
    MAX_MONTHLY_POSTS: int = 500
    CSV_PATH: str
    TZ: str

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
