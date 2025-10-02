from pydantic_settings import BaseSettings
from typing import Optional, List, Union

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost/medical_exam_db"

    # CORS
    # Comma-separated list or * for all
    CORS_ORIGINS: Union[str, List[str]] = "*"
    
    # Email settings
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
