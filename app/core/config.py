from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_API_KEY: str | None
    OPENAI_API_KEY: str | None
    FILE_SNAPSHOT: bool = True
    LOG_LEVEL: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings() # type: ignore