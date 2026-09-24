"""
Loads app configuration from environment variables.

Every guardrail threshold (max input length, injection confidence cutoff)
lives here instead of being hardcoded inside guardrail files. This keeps
config changes to a one-line .env edit instead of a code change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_model: str
    app_env: str
    log_level: str
    max_input_length: int
    injection_confidence_threshold: float

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            app_env=os.getenv("APP_ENV", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_input_length=int(os.getenv("MAX_INPUT_LENGTH", "4000")),
            injection_confidence_threshold=float(
                os.getenv("INJECTION_CONFIDENCE_THRESHOLD", "0.7")
            ),
        )


settings = Settings.load()
