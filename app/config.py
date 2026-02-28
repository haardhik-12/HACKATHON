"""
config.py — Centralized configuration loader.
Reads all settings from environment variables (via .env file).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")          # ollama | groq | openai | mock
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # Crisis & Session
    DEFAULT_CRISIS_COUNTRY: str = os.getenv("DEFAULT_CRISIS_COUNTRY", "US")
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "1800"))

    # MongoDB persistence
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "mental_health_db")

    # App
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-me-in-production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # File paths (relative to project root)
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    SUPPORT_LIBRARY_PATH: str = os.path.join(DATA_DIR, "support_library.json")
    CRISIS_RESOURCES_PATH: str = os.path.join(DATA_DIR, "crisis_resources.json")


config = Config()
