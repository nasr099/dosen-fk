from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List, Union

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost/medical_exam_db"

    # Validator otomatis untuk mengubah 'postgres://' menjadi 'postgresql://'
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "*"
    
    # Storage (DigitalOcean Spaces)
    DO_SPACES_BUCKET: Optional[str] = None
    DO_SPACES_REGION: Optional[str] = None
    DO_SPACES_ENDPOINT: Optional[str] = None
    DO_SPACES_KEY: Optional[str] = None
    DO_SPACES_SECRET: Optional[str] = None

    # Public CDN base
    PUBLIC_CDN_BASE: Optional[str] = None
    
    # Email settings
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # LLM providers
    OPENAI_API_KEY: Optional[str] = None
    
    # pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra='ignore',
        case_sensitive=True # Memastikan nama variabel match dengan Environment Variable
    )

settings = Settings()
