"""
Dependencias de la capa PRIVADA (el guardián del panel interno).

get_current_user es la dependencia que se engancha a las rutas privadas:
en cada petición lee el token JWT de la cabecera Authorization, lo verifica,
y devuelve el usuario autenticado. Si el token falta, es inválido o expiró,
corta la petición con un 401 ANTES de que el endpoint se ejecute.

require_admin exige además que el usuario tenga rol de administrador (403 si no).

Así, proteger una ruta es tan simple como declarar la dependencia; es
imposible olvidarla y dejar una ruta abierta por descuido.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decodificar_token
from app.modules.usuarios.model import RolUsuario, Usuario
from app.modules.usuarios.repository import UsuarioRepository

# Le dice a FastAPI de dónde sacar el token (cabecera Authorization: Bearer ...).
# tokenUrl apunta al endpoint de login (para la documentación /docs).
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Verifica el token y devuelve el usuario autenticado.
    Se ejecuta ANTES del endpoint; si algo falla, lanza 401 y el endpoint
    nunca corre.
    """
    credenciales_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None:
        raise credenciales_error

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise credenciales_error

    usuario = UsuarioRepository(db).get(int(usuario_id))
    if usuario is None or not usuario.activo:
        raise credenciales_error

    return usuario


def require_admin(
    usuario: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Exige que el usuario autenticado sea administrador.
    Se apoya en get_current_user (dependencias anidadas): primero valida el
    token, luego el rol. Lanza 403 si no es admin.
    """
    if usuario.rol != RolUsuario.administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere permisos de administrador",
        )
    return usuario