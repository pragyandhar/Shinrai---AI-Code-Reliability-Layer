# WHAT DOES THIS FILE DO: Loads all env variables and makes them available as one settings object across the app.

# ================== IMPORTS ==================
from pydantic_settings import BaseSettings, SettingsConfigDict
# ================== IMPORTS ==================


# =========== VARIABLES : App-wide settings loaded from .env ===========
class Settings(BaseSettings):
    ''' All config in one place — pulled from .env automatically '''

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Azure AI Foundry
    foundry_endpoint: str
    foundry_deployment: str
    foundry_api_key: str
    azure_openai_api_version: str

    # Redis
    redis_url: str
    redis_api: str

    # Database
    database_url: str

    # App behaviour
    sandbox_mode: str
    max_repair_attempts: int


settings = Settings()   # USE: import this one object everywhere, don't use os.getenv() anywhere
# =========== VARIABLES : App-wide settings loaded from .env ===========