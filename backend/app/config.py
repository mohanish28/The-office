from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://office:office@localhost:5432/office"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    NIM_API_KEY_ENCRYPTION_KEY: str
    BEHIND_PROXY: bool = False
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
