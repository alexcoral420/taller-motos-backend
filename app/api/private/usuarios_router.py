"""
Router PRIVADO de gestión de usuarios.

Solo el ADMINISTRADOR puede gestionar usuarios (crear técnicos, listarlos,
etc.). Por eso todas las rutas usan Depends(require_admin): si un técnico
autenticado intenta entrar aquí, recibe 403.

Rutas finales (se monta bajo /api/v1):
    POST /api/v1/usuarios        -> crear usuario (técnico o admin)
    GET  /api/v1/usuarios        -> listar usuarios
    GET  /api/v1/usuarios/{id}   -> ver un usuario
    PATCH /api/v1/usuarios/{id}  -> actualizar un usuario
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.private.deps import require_admin
from app.core.database import get_db
from app.modules.usuarios.model import Usuario
from app.modules.usuarios.schema import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.modules.usuarios.service import (
    EmailDuplicado,
    UsuarioNoEncontrado,
    UsuarioService,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios (admin)"])


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),   # solo admin
):
    """Crea un usuario (técnico o administrador)."""
    service = UsuarioService(db)
    try:
        return service.crear(data)
    except EmailDuplicado as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Lista todos los usuarios."""
    service = UsuarioService(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Devuelve un usuario por su id."""
    service = UsuarioService(db)
    try:
        return service.obtener(usuario_id)
    except UsuarioNoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Actualiza un usuario (datos, rol, contraseña, activo/inactivo)."""
    service = UsuarioService(db)
    try:
        return service.actualizar(usuario_id, data)
    except UsuarioNoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmailDuplicado as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))