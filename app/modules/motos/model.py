"""
Modelo del módulo de motos (tabla: motocicletas).

Necesario para que SQLAlchemy resuelva la llave foránea de
ordenes_trabajo.moto_id. Aunque en el registro rápido no siempre se crea
una fila de moto, la clase debe existir para el mapeo de relaciones.
"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, PKMixin, TimestampMixin


class Motocicleta(Base, PKMixin, TimestampMixin):
    __tablename__ = "motocicletas"

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False
    )
    placa: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    marca: Mapped[str | None] = mapped_column(Text)
    modelo: Mapped[str | None] = mapped_column(Text)
    cilindraje: Mapped[int | None] = mapped_column(Integer)
    anio: Mapped[int | None] = mapped_column(Integer)
    vin: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(Text)
    km_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Motocicleta {self.placa}>"