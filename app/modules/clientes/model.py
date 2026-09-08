"""
Modelo del módulo de clientes (tabla: clientes).

Incluye tanto clientes formales del taller como prospectos/leads que entran
por la web. El consentimiento (acepta_publicidad + fecha) es clave para el
seguimiento y las campañas, y cumple con habeas data (Ley 1581).
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Enum as SqlEnum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, PKMixin, TimestampMixin


class OrigenCliente(str, enum.Enum):
    """Coincide con el enum 'origen_cliente' del esquema SQL."""
    taller = "taller"
    web = "web"
    referido = "referido"
    otro = "otro"


class CanalContacto(str, enum.Enum):
    """Coincide con el enum 'canal_contacto' del esquema SQL."""
    whatsapp = "whatsapp"
    sms = "sms"
    email = "email"
    llamada = "llamada"


class Cliente(Base, PKMixin, TimestampMixin):
    __tablename__ = "clientes"

    tipo_documento: Mapped[str | None] = mapped_column(Text)
    numero_documento: Mapped[str | None] = mapped_column(Text, unique=True)
    nombres: Mapped[str] = mapped_column(Text, nullable=False)
    apellidos: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    direccion: Mapped[str | None] = mapped_column(Text)
    ciudad: Mapped[str | None] = mapped_column(Text)

    origen: Mapped[OrigenCliente] = mapped_column(
        SqlEnum(OrigenCliente, name="origen_cliente", create_type=False),
        nullable=False,
        default=OrigenCliente.taller,
    )

    # Consentimiento para publicidad / seguimiento (habeas data).
    acepta_publicidad: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    canal_preferido: Mapped[CanalContacto | None] = mapped_column(
        SqlEnum(CanalContacto, name="canal_contacto", create_type=False)
    )
    fecha_consentimiento: Mapped[datetime | None] = mapped_column()
    medio_consentimiento: Mapped[str | None] = mapped_column(Text)

    notas: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Cliente {self.nombres} {self.apellidos or ''}>"