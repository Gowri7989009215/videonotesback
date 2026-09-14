"""
Application settings using pydantic-settings.
Reads environment variables from .env file.
"""

from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    node_env: str = "development"
    port: int = 4000
    host: str = "0.0.0.0"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/videonotes"

    jwt_secret: str = "secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_in_hours: int = 168  # 7 days

    resend_api_key: str = ""
    email_from: str = "noreply@videonotes.ai"
    gmail_user: str = ""
    gmail_pass: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""

    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    vosk_model_path: str = ""
    whisper_model_name: str = "small"

    storage_root: str = "storage"
    require_email_verification: bool = False

    ytdlp_proxy: str = ""
    ytdlp_cookies_path: str = ""

    allowed_origins: str = "http://localhost:5173,http://localhost:3000,https://videonotesback.onrender.com,https://videonotesfront.vercel.app"
    @property
    def is_prod(self) -> bool:
        return self.node_env == "production"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def asyncpg_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            return url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
