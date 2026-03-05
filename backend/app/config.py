
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "mysql+asyncmy://root:secret@localhost:3306/virtual_queue"

 
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Worker (Procesador de Cola) ---
    BATCH_SIZE: int = 10        
    PROCESS_INTERVAL: int = 1   
    ALLOWED_TTL: int = 300      
    # --- Reconexión WebSocket ---
    RECONNECT_GRACE_PERIOD: int = 30  

    class Config:
        env_file = ".env"              
        env_file_encoding = "utf-8"
        case_sensitive = True



settings = Settings()
