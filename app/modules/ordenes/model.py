"""
Modelos del módulo de órdenes de trabajo.

Dos tablas:
  - ordenes_trabajo : la orden que registra el técnico.
  - ot_items        : cada servicio de la orden, con el VALOR COBRADO que
                      escribe el técnico (negociable, no copiado del catálogo).

Tipos de orden:
  - interno : moto del inventario de la compraventa. Solo requiere placa
              (vínculo con el otro sistema). Es un COSTO de acondicionamiento.
  - externo : moto de un cliente de la calle. Lleva cliente + datos de moto.
              Es un INGRESO del taller.

Sin estados por ahora (se añadirán después).
"""

import enum
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Enum as SqlEnum,
    FetchedValue,
    ForeignKey,
    Numeric,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base.base_model import Base, CreatedAtMixin, PKMixin, TimestampMixin


class TipoOrden(str, enum.Enum):
    """Coincide con el enum 'tipo_orden' del esquema SQL."""
    interno = "interno"
    externo = "externo"


class TipoItemOt(str, enum.Enum):
    """Coincide con el enum 'tipo_item_ot' del esquema SQL."""
    mano_obra = "mano_obra"
    repuesto = "repuesto"


class OrdenTrabajo(Base, PKMixin, TimestampMixin):
    __tablename__ = "ordenes_trabajo"

    # Consecutivo humano (lo genera la base con IDENTITY).
    numero: Mapped[int] = mapped_column(
    BigInteger, unique=True, server_default=FetchedValue()
)

    tipo: Mapped[TipoOrden] = mapped_column(
        SqlEnum(TipoOrden, name="tipo_orden", create_type=False),
        nullable=False,
        default=TipoOrden.externo,
    )

    # Placa: protagonista. Obligatoria en internas (vínculo con la compraventa),
    # muy recomendada en externas. A nivel de base es opcional para flexibilidad;
    # la obligatoriedad por tipo se valida en el service.
    placa: Mapped[str | None] = mapped_column(Text)

    # Opcionales: las internas no tienen cliente; la moto puede no ser una fila.
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id", ondelete="SET NULL")
    )
    moto_id: Mapped[int | None] = mapped_column(
        ForeignKey("motocicletas.id", ondelete="SET NULL")
    )

    # Técnico que registró la orden (para su comisión).
    tecnico_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    sintoma: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)

    # Totales congelados (los calcula el service al agregar los ítems).
    total_mano_obra: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    total_repuestos: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    observaciones: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["OtItem"]] = relationship(
        back_populates="orden",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<OrdenTrabajo #{self.numero} {self.tipo.value} placa={self.placa}>"


class OtItem(Base, PKMixin, CreatedAtMixin):
    __tablename__ = "ot_items"

    orden_id: Mapped[int] = mapped_column(
        ForeignKey("ordenes_trabajo.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[TipoItemOt] = mapped_column(
        SqlEnum(TipoItemOt, name="tipo_item_ot", create_type=False),
        nullable=False,
        default=TipoItemOt.mano_obra,
    )

    # Servicio del catálogo (si es mano de obra).
    catalogo_servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalogo_servicios.id")
    )
    # Repuesto del inventario (para la versión 2; por ahora null).
    repuesto_id: Mapped[int | None] = mapped_column(
        ForeignKey("repuestos.id")
    )

    # Técnico que ejecutó este ítem (para comisión).
    tecnico_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)

    # VALOR COBRADO que escribe el técnico (negociable).
    valor_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # Comisión congelada al momento de crear el ítem.
    comision_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    comision_valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    orden: Mapped["OrdenTrabajo"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<OtItem {self.descripcion} x{self.cantidad}>"