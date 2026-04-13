from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Configurações da aplicação utilizando pydantic-settings."""
    
    # API Metadata
    PROJECT_NAME: str = "Desafio NL Consulting API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Configurações de Banco de Dados
    # Valor padrão: SQLite assíncrono para facilitar o desenvolvimento inicial
    DATABASE_URL: str = ""
    
    # Configurações de IA (necessário preencher no .env)
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # Segurança
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
