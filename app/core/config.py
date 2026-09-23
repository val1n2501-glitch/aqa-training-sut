"""Explicit environment configuration; no implicit .env loading."""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'tasks.db'}"
    test_mode: bool = False

    @field_validator("database_url")
    @classmethod
    def file_sqlite_only(cls, value: str) -> str:
        if not value.startswith("sqlite:///") or value == "sqlite:///:memory:":
            raise ValueError("Use a file SQLite URL: sqlite:///path/to/tasks.db")
        if not value.removeprefix("sqlite:///") or "?" in value:
            raise ValueError("SQLite file path must be nonempty and contain no query")
        return value

    @classmethod
    def from_env(cls) -> "Settings":
        values = {
            name: os.environ[name.upper()]
            for name in cls.model_fields
            if name.upper() in os.environ
        }
        return cls(**values)
