"""
Modelo del módulo de pagos (tabla: pagos).

Registra el cobro de una orden. Diseñado para crecer hacia una pasarela:
  - Hoy (manual): estado='confirmado', origen='manual'.
  - Mañana (pasarela): estado='pendiente' -> 'confirmado' vía webhook,
    origen='pasarela', y 'referencia' con el id de transacción.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, CreatedAtMixin, PKMixin


class MetodoPago(str, enum.Enum):
    efectivo = "efectivo"
    nequi = "nequi"
    daviplata = "daviplata"
    breve = "breve"


class EstadoPago(str, enum.Enum):
    pendiente = "pendiente"
    confirmado = "confirmado"
    fallido = "fallido"


class OrigenPago(str, enum.Enum):
    manual = "manual"
    pasarela = "pasarela"


class Pago(Base, PKMixin, CreatedAtMixin):
    __tablename__ = "pagos"

    # Identificador opaco para el enlace del recibo (no el id interno).
    public_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4
    )

    orden_id: Mapped[int] = mapped_column(
        ForeignKey("ordenes_trabajo.id", ondelete="RESTRICT"), nullable=False
    )
    # Quién cobró (el mismo técnico que registró la orden).
    tecnico_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    metodo: Mapped[MetodoPago] = mapped_column(
        SqlEnum(MetodoPago, name="metodo_pago", create_type=False), nullable=False
    )
    estado: Mapped[EstadoPago] = mapped_column(
        SqlEnum(EstadoPago, name="estado_pago", create_type=False),
        nullable=False,
        default=EstadoPago.confirmado,
    )
    origen: Mapped[OrigenPago] = mapped_column(
        SqlEnum(OrigenPago, name="origen_pago", create_type=False),
        nullable=False,
        default=OrigenPago.manual,
    )

    # Para la pasarela futura (id de transacción). Hoy vacío.
    referencia: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Pago orden={self.orden_id} {self.metodo.value} ${self.monto}>"