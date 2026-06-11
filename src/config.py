from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "AI20K-162 Task Planner"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000"

    # LLM — provider switch: "gemini" (mặc định, cloud) | "ollama" (local).
    # Đặt LLM_PROVIDER=ollama trong .env để chạy local TẠM THỜI trên máy này;
    # mặc định code vẫn là gemini nên không phải thay đổi vĩnh viễn.
    llm_provider: Literal["gemini", "ollama"] = "gemini"

    # LLM — Gemini (cloud)
    gemini_api_key: str = ""
    model_name: str = "gemini-2.0-flash"
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # LLM — Ollama (local). Cần model hỗ trợ tool-calling (qwen2.5 / llama3.1).
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Agent safety caps
    max_steps: int = 40
    max_replans: int = 5
    # Scope v2 'thu nhỏ': True -> bỏ replan/ask_human, chỉ vòng lõi
    core_scope: bool = False

    # AI Logs — LangSmith (deliverable #4)
    langchain_api_key: str = ""
    langchain_project: str = "ai20k-162-agent"
    langchain_tracing_v2: str = "false"


@lru_cache
def get_settings() -> Settings:
    return Settings()
