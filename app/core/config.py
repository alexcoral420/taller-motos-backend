"""
Configuración central de la aplicación.

Lee TODAS las variables sensibles desde el entorno (archivo .env en local,
variables de entorno en Railway). Nada de secretos hardcodeados en el repo.

Uso en cualquier parte del proyecto:
    from app.core.config import settings
    settings.DATABASE_URL
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # ignora variables de entorno no declaradas aquí
    )

    # ------------------------------------------------------------------
    #  Aplicación
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "Taller Motos API"
    ENVIRONMENT: str = "development"        # development | production
    DEBUG: bool = False

    # Prefijos que separan los dos mundos (ver main.py)
    API_V1_PREFIX: str = "/api/v1"          # panel interno (privado)
    API_PUBLIC_PREFIX: str = "/api/public"  # sitio web (público)

    # ------------------------------------------------------------------
    #  Base de datos — Supabase (usar SIEMPRE el connection pooler)
    #  Formato con SQLAlchemy + psycopg2:
    #  postgresql+psycopg2://postgres.<ref>:<pass>@aws-0-<region>.pooler.supabase.com:6543/postgres
    #  Sin valor por defecto: si falta, la app falla al arrancar (deseable).
    # ------------------------------------------------------------------
    DATABASE_URL: str

    # ------------------------------------------------------------------
    #  Seguridad / JWT  (los usa core/security.py y la capa privada)
    # ------------------------------------------------------------------
    SECRET_KEY: str                          # generar con: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 días

        # Se leen como texto separado por comas y se convierten a lista en las
    # propiedades de abajo (evita que pydantic-settings intente parsear JSON).
    PUBLIC_CORS_ORIGINS: str = ""      # tu web pública
    PRIVATE_CORS_ORIGINS: str = ""     # tu panel interno (SPA)

    # ------------------------------------------------------------------
    #  Rate limiting de la capa pública (slowapi)
    # ------------------------------------------------------------------
    PUBLIC_RATE_LIMIT: str = "20/minute"     # límite por IP para POST públicos

    @property
    def public_cors_list(self) -> list[str]:
        return [o.strip() for o in self.PUBLIC_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def private_cors_list(self) -> list[str]:
        return [o.strip() for o in self.PRIVATE_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Instancia única cacheada (evita releer el entorno en cada import)."""
    return Settings()


# Instancia lista para importar en todo el proyecto
settings = get_settings()