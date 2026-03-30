"""Repository helpers for generic persisted app settings."""

from __future__ import annotations

import json

from database.connection import get_connection
from database.defaults import PERSISTED_STATE_DEFAULTS


def load_app_settings() -> dict:
    """Load persisted app-level settings from SQLite."""
    with get_connection() as connection:
        rows = connection.execute("SELECT key, value_json FROM app_config").fetchall()

    settings = {row["key"]: json.loads(row["value_json"]) for row in rows}
    for key, default_value in PERSISTED_STATE_DEFAULTS.items():
        settings.setdefault(key, default_value)
    return settings


def save_app_setting(key: str, value) -> None:
    """Persist a single app-level setting."""
    with get_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO app_config (key, value_json) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        connection.commit()


def save_app_settings(settings: dict) -> None:
    """Persist multiple app-level settings in one transaction."""
    with get_connection() as connection:
        for key, value in settings.items():
            connection.execute(
                "INSERT OR REPLACE INTO app_config (key, value_json) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        connection.commit()
