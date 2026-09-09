"""
Modelo del módulo de inventario (tabla: repuestos).

Necesario para que SQLAlchemy resuelva la llave foránea de
ot_items.repuesto_id. El uso completo de repuestos (descuento de stock en
las órdenes) llegará en la versión 2; por ahora la clase debe existir para
el mapeo de relaciones.
"""

from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, PKMixin, TimestampMixin


class Repuesto(Base, PKMixin, TimestampMixin):
    __tablename__ = "repuestos"

    codigo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    precio_venta: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    ubicacion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Repuesto {self.codigo} - {self.descripcion}>"