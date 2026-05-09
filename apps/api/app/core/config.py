from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = ROOT / "configs"
DATA_DIR = ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8787
    log_level: str = "INFO"

    # LLM
    openai_api_key: str | None = None
    default_model: str = "gpt-5.4"
    backup_model: str = "gpt-4o"

    # YouTube
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    youtube_refresh_token: str | None = None
    youtube_channel_id: str | None = None

    # Azure Speech
    azure_speech_key: str | None = None
    azure_speech_region: str = "koreacentral"

    # Fal
    fal_key: str | None = None

    # Search
    naver_client_id: str | None = None
    naver_client_secret: str | None = None
    google_api_key: str | None = None
    youtube_api_key: str | None = None

    @property
    def effective_youtube_api_key(self) -> str | None:
        return self.youtube_api_key or self.google_api_key

    # DB
    database_url: str = f"sqlite:///{DATA_DIR}/youtube.db"

    # Paths
    obsidian_vault: str = "/Users/yosiki/Documents/Obsidian Vault/wiki/YouTube 자동화프로젝트"
    data_dir: Path = DATA_DIR

    # Web
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3737", "http://localhost:3000"]
    )

    # Channel (from configs/config.yaml)
    channel_name: str = "리치고"
    share_link: str = "https://share.note.sx/qynhdluo"

    @property
    def project_config(self) -> dict:
        path = CONFIG_DIR / "config.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def channel_profile(self) -> dict:
        path = CONFIG_DIR / "channel_richgo.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @property
    def scoring_rules(self) -> dict:
        path = CONFIG_DIR / "scoring.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


@lru_cache
def _settings() -> Settings:
    s = Settings()
    cfg = s.project_config
    if cfg.get("channel_name"):
        s.channel_name = cfg["channel_name"]
    if cfg.get("share_link"):
        s.share_link = cfg["share_link"]
    if cfg.get("default_model"):
        s.default_model = cfg["default_model"]
    if cfg.get("backup_model"):
        s.backup_model = cfg["backup_model"]
    s.data_dir.mkdir(parents=True, exist_ok=True)
    return s


settings = _settings()
