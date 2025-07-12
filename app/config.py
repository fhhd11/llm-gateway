from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    lite_llm_markup: float = 0.25
    redis_url: str = "redis://localhost:6379"
    langfuse_secret_key: str | None = None
    jwt_secret: str

    class Config:
        env_file = ".env"

settings = Settings()