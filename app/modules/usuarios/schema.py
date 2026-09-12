"""
Schemas del módulo de usuarios.

Principio de seguridad clave: la CONTRASEÑA entra (al crear/actualizar) pero
el HASH NUNCA sale. Fíjate que UsuarioOut no tiene password ni password_hash.
Aunque el service devuelva el objeto completo del ORM, el response_model
recorta la salida y el hash jamás llega al cliente.

También hay schemas para el login (credenciales de entrada y el token de
salida).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.usuarios.model import RolUsuario


# ---------------------------------------------------------------------------
#  Entrada
# ---------------------------------------------------------------------------
class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=72)  # entra en claro, se hashea en el service
    rol: RolUsuario = RolUsuario.tecnico
    comision_pct_default: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class UsuarioUpdate(BaseModel):
    """Actualización parcial. La contraseña es opcional (solo si se cambia)."""
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    rol: RolUsuario | None = None
    comision_pct_default: Decimal | None = Field(default=None, ge=0, le=100)
    activo: bool | None = None


# ---------------------------------------------------------------------------
#  Salida  (NUNCA incluye password ni password_hash)
# ---------------------------------------------------------------------------
class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    rol: RolUsuario
    comision_pct_default: Decimal
    activo: bool
    created_at: datetime


# ---------------------------------------------------------------------------
#  Login
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    """Lo que devolvemos tras un login exitoso."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut