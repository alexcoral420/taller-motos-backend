"""
Modelos del módulo de cotizaciones (leads que entran por la web pública).

Dos tablas:
  - cotizaciones      : la solicitud que llena el cliente en el sitio.
  - cotizacion_items  : los servicios del catálogo que seleccionó, con su
                        precio de referencia CONGELADO al momento de pedir.

Un lead puede convertirse luego en cliente formal (cliente_id) desde el
panel del administrador.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base.base_model import Base, CreatedAtMixin, PKMixin, TimestampMixin


class EstadoCotizacion(str, enum.Enum):
    """Coincide con el enum 'estado_cotizacion' del esquema SQL."""
    nueva = "nueva"
    en_proceso = "en_proceso"
    respondida = "respondida"
    convertida = "convertida"
    descartada = "descartada"


class Cotizacion(Base, PKMixin, TimestampMixin):
    __tablename__ = "cotizaciones"

    # Identificador opaco que SÍ se puede exponer al público (no el id interno).
    public_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4
    )

    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    telefono: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    modelo_moto: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)

    estado: Mapped[EstadoCotizacion] = mapped_column(
        SqlEnum(EstadoCotizacion, name="estado_cotizacion", create_type=False),
        nullable=False,
        default=EstadoCotizacion.nueva,
    )

    # Se llena cuando el admin convierte el lead en cliente formal.
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id", ondelete="SET NULL")
    )

    # Consentimiento de contacto (habeas data).
    acepta_publicidad: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    fecha_consentimiento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Para auditoría / control anti-spam.
    ip_origen: Mapped[str | None] = mapped_column(INET)

    # Relación con los ítems (servicios seleccionados).
    items: Mapped[list["CotizacionItem"]] = relationship(
        back_populates="cotizacion",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Cotizacion {self.public_token} - {self.nombre}>"


class CotizacionItem(Base, PKMixin, CreatedAtMixin):
    __tablename__ = "cotizacion_items"

    cotizacion_id: Mapped[int] = mapped_column(
        ForeignKey("cotizaciones.id", ondelete="CASCADE"), nullable=False
    )
    catalogo_servicio_id: Mapped[int] = mapped_column(
        ForeignKey("catalogo_servicios.id"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=1
    )
    precio_referencia: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    cotizacion: Mapped["Cotizacion"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<CotizacionItem servicio={self.catalogo_servicio_id}>"