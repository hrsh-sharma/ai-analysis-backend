from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/ai_reviewer"
    REDIS_URL: str = "redis://localhost:6379"
    GROQ_API_KEY: str = "your-groq-key-here"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
