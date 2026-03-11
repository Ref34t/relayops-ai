from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    app_name: str = "RelayOps AI"
    database_path: Path = Path("data/relayops.db")
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    slack_webhook_url: Optional[str] = None
    hubspot_private_app_token: Optional[str] = None
    hubspot_base_url: str = "https://api.hubapi.com"


def get_settings() -> Settings:
    return Settings(
        database_path=Path(os.getenv("RELAYOPS_DB_PATH", "data/relayops.db")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
        hubspot_private_app_token=os.getenv("HUBSPOT_PRIVATE_APP_TOKEN"),
        hubspot_base_url=os.getenv("HUBSPOT_BASE_URL", "https://api.hubapi.com"),
    )
