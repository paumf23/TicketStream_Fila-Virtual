
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):

    REDIS_URL: str = "redis://redis:6379/0"
    DATABASE_URL: str = "mysql+asyncmy://root:secret@db:3306/virtual_queue"

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

# ===============================================================
# Worker (Procesador de Cola)   
# ===============================================================
    BATCH_SIZE: int = 10
    PROCESS_INTERVAL: int = 1
    ALLOWED_TTL: int = 120

# ===============================================================
# Reconexión WebSocket
# ===============================================================
    RECONNECT_GRACE_PERIOD: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# ===============================================================
# Guardia de Seguridad para Producción
# ===============================================================
# Si ENVIRONMENT=production, la app se rehúsa a arrancar con
# credenciales de desarrollo (root:secret) o CORS apuntando a
# localhost. Esto previene despliegues accidentalmente inseguros.
# ===============================================================
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if "root:secret" in self.DATABASE_URL:
                raise ValueError(
                    "❌ DATABASE_URL contiene credenciales por defecto (root:secret). "
                    "Configure variables de entorno seguras en el archivo .env para producción."
                )
            if "localhost" in self.CORS_ORIGINS:
                raise ValueError(
                    "❌ CORS_ORIGINS apunta a localhost en modo producción. "
                    "Configure la IP o dominio real del servidor en el archivo .env."
                )
        return self

settings = Settings()
