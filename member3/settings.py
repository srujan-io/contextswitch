"""Centralized environment and Gemini client setup; never logs credentials."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


ENV_FILE = Path(__file__).with_name(".env")
GEMINI_TIMEOUT_MS = 10_000  # Gemini rejects shorter explicit deadlines.


def _load_local_env() -> None:
    """Load this package's .env once; allow operation without python-dotenv."""
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE, override=False)
        return
    except ImportError:
        pass
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        value = line.strip()
        if not value or value.startswith("#") or "=" not in value:
            continue
        key, content = value.split("=", 1)
        os.environ.setdefault(key.strip(), content.strip().strip("\"'"))


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    embedding_model: str


def load_settings() -> Settings:
    _load_local_env()
    return Settings(
        api_key=os.environ.get("GEMINI_API_KEY"),
        model=os.environ.get("GEMINI_MODEL", "gemini-3.8-flash"),
        embedding_model=os.environ.get("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5"),
    )


def create_gemini_client(settings: Settings | None = None):
    settings = settings or load_settings()
    if not settings.api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in member3/.env")
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed; install member3/requirements.txt") from exc
    return genai.Client(
        api_key=settings.api_key,
        http_options=types.HttpOptions(
            timeout=GEMINI_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
