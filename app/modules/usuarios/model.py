"""
Modelo del módulo de usuarios (tabla: usuarios).

Los usuarios internos del sistema: técnicos y administrador. Cada uno tiene
un rol que define a qué partes del panel privado puede acceder.

Nunca se guarda la contraseña en texto plano: la columna password_hash
almacena el hash generado por core/security.py.
"""

import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum as SqlEnum, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, PKMixin, TimestampMixin


class RolUsuario(str, enum.Enum):
    """Coincide con el enum 'rol_usuario' del esquema SQL."""
    tecnico = "tecnico"
    administrador = "administrador"


class Usuario(Base, PKMixin, TimestampMixin):
    __tablename__ = "usuarios"

    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # Guarda el HASH de la contraseña, nunca la contraseña en texto plano.
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    rol: Mapped[RolUsuario] = mapped_column(
        SqlEnum(RolUsuario, name="rol_usuario", create_type=False),
        nullable=False,
        default=RolUsuario.tecnico,
    )

    # % de comisión por defecto sobre la mano de obra de este técnico.
    comision_pct_default: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0
    )

    # Permite desactivar un usuario sin borrarlo (pierde el acceso).
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.rol.value})>"