from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot
    BOT_TOKEN: str = Field(default="YOUR_BOT_TOKEN_HERE")
    WEBAPP_URL: str = Field(default="https://example.com")

    # PostgreSQL
    POSTGRES_USER: str = Field(default="astro_user")
    POSTGRES_PASSWORD: str = Field(default="astro_pass")
    POSTGRES_DB: str = Field(default="astro_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://astro_user:astro_pass@localhost:5432/astro_db"
    )

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # OpenRouter AI
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_MODEL: str = Field(default="qwen/qwen-2.5-72b-instruct")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # Business rules / Pricing
    PRO_PRICE_STARS: int = Field(default=150)  # ~299 RUB equivalent in Stars
    FREE_DAILY_TAROT: int = Field(default=1)
    FREE_DAILY_AI_QUESTIONS: int = Field(default=1)


settings = Settings()
