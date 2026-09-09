"""
Funciones de seguridad: hasheo de contraseñas y tokens JWT.

Este módulo NO sabe de HTTP ni de la base de datos. Solo provee las
herramientas criptográficas que usarán el service de usuarios (para
verificar credenciales) y las dependencias privadas (para validar tokens).

Dos responsabilidades:
  1. Contraseñas: hashear (al crear usuario) y verificar (al hacer login).
     Nunca se guarda la contraseña en texto plano, solo su hash.
  2. Tokens JWT: crear (al hacer login) y decodificar (en cada petición
     protegida).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Contexto de hasheo. bcrypt es un algoritmo lento a propósito: dificulta
# los ataques de fuerza bruta contra las contraseñas.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
#  Contraseñas
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Convierte una contraseña en texto plano a un hash seguro para guardar."""
    return pwd_context.hash(password)


def verify_password(password_plano: str, password_hash: str) -> bool:
    """Compara una contraseña ingresada con el hash guardado. True si coincide."""
    return pwd_context.verify(password_plano, password_hash)


# ---------------------------------------------------------------------------
#  Tokens JWT
# ---------------------------------------------------------------------------
def crear_access_token(
    subject: str | int, extra: dict[str, Any] | None = None
) -> str:
    """
    Crea un token JWT firmado.

    - subject: identifica al usuario (usamos su id).
    - extra: datos adicionales a incluir (p.ej. el rol).
    El token lleva una fecha de expiración; pasado ese tiempo, deja de valer.
    """
    ahora = datetime.now(timezone.utc)
    expira = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),   # 'subject': a quién pertenece el token
        "iat": ahora,          # 'issued at': cuándo se emitió
        "exp": expira,         # 'expiration': cuándo caduca
    }
    if extra:
        payload.update(extra)

    # Se firma con el SECRET_KEY. Sin esa clave, nadie puede falsificar
    # un token válido.
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any] | None:
    """
    Verifica y decodifica un token JWT.
    Devuelve el payload si el token es válido y no ha expirado; None si es
    inválido, fue manipulado o caducó.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None