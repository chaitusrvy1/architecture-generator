from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Architecture Generator API"
    environment: str = "development"

    # OpenAI (Standard)
    openai_api_key: str = ""
    openai_model_name: str = "gpt-4o"

    # Google Gemini
    google_api_key: str = ""

    # Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment_name: str = ""

    # Cosmos DB
    cosmos_db_endpoint: str = ""
    cosmos_db_key: str = ""
    cosmos_db_database_name: str = ""
    cosmos_db_container_name: str = ""

    # Validation
    kroki_api_url: str = "https://kroki.io/"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
