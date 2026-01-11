from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_PRESIGNED_URL_EXPIRATION: int = 3600  # 1 hour

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_API_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None


settings = Settings()
