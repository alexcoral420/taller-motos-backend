"""
Router de autenticación (login) de la capa privada.

Aquí el usuario entrega sus credenciales y, si son válidas, recibe su token
JWT. Ese token es el que luego el guardián (get_current_user) verifica en
cada petición protegida.

Rutas finales (se monta bajo /api/v1):
    POST /api/v1/auth/login   -> login con formulario (compatible con /docs)
    GET  /api/v1/auth/me      -> datos del usuario autenticado
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.private.deps import get_current_user
from app.core.database import get_db
from app.modules.usuarios.model import Usuario
from app.modules.usuarios.schema import TokenResponse, UsuarioOut
from app.modules.usuarios.service import CredencialesInvalidas, UsuarioService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login con formulario estándar OAuth2 (usuario = email, contraseña).
    Este formato permite probar el login desde /docs con el botón Authorize.
    """
    service = UsuarioService(db)
    try:
        # OAuth2PasswordRequestForm usa el campo 'username'; ahí va el email.
        token, usuario = service.autenticar(form.username, form.password)
    except CredencialesInvalidas as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=token,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioOut)
def usuario_actual(usuario: Usuario = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado (según su token)."""
    return usuario