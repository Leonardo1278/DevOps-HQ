from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _API_DIR.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_API_DIR / ".env", _REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://leo:leo@localhost:5433/leo_hq"
    cors_origins: str = "http://localhost:3000"
    aws_region: str = "us-east-1"
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    s3_bucket: str = ""
    openai_api_key: str = ""
    dev_auth_bypass: bool = True
    api_public_url: str = "http://127.0.0.1:8000"
    local_upload_dir: str = ".data/uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def resolved_upload_dir(self) -> Path:
        path = Path(self.local_upload_dir)
        if not path.is_absolute():
            path = _API_DIR / path
        return path.resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
