"""
Dependencia de autenticación para la capa de INTEGRACIÓN.

A diferencia del panel (que usa JWT de usuario), los sistemas externos
(la compraventa) se autentican con una API Key fija enviada en el header
X-API-Key. Es el mecanismo estándar para comunicación máquina a máquina.
"""

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verificar_api_key(x_api_key: str = Header(default="")) -> None:
    """
    Valida la API Key del header X-API-Key contra la configurada.
    Si no coincide (o no está configurada), corta con 401.
    """
    # Si no hay clave configurada en el servidor, negamos todo por seguridad.
    if not settings.INTEGRACION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integración no configurada",
        )

    if x_api_key != settings.INTEGRACION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
        )