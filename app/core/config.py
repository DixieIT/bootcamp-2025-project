from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    FILE_SNAPSHOT: bool = True
    USE_DATABASE: bool = True  # Use SQLite instead of in-memory/file
    DATABASE_PATH: str = "var/database.db"
    LOG_LEVEL: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()