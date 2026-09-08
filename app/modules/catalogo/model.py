"""
Modelo del catálogo de servicios (tabla: catalogo_servicios).

Cada servicio ofrecido por el taller. Los que tienen visible_publico=True
son los que se exponen en la web pública. Los campos intervalo_dias /
intervalo_km alimentan el motor de recordatorios de recompra.
"""

import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum as SqlEnum, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, PKMixin, TimestampMixin


class TipoServicio(str, enum.Enum):
    """Coincide con el tipo enum 'tipo_servicio' del esquema SQL."""
    mano_obra = "mano_obra"
    diagnostico = "diagnostico"
    revision = "revision"


class CatalogoServicio(Base, PKMixin, TimestampMixin):
    __tablename__ = "catalogo_servicios"

    codigo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)

    tipo: Mapped[TipoServicio] = mapped_column(
        # El tipo enum YA existe en la base -> create_type=False para que
        # SQLAlchemy no intente crearlo de nuevo.
        SqlEnum(TipoServicio, name="tipo_servicio", create_type=False),
        nullable=False,
        default=TipoServicio.mano_obra,
    )

    precio_referencia: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # Se muestra en la web pública si es True (precio "desde $X").
    visible_publico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Reglas de mantenimiento para los recordatorios de recompra.
    intervalo_dias: Mapped[int | None] = mapped_column(Integer)
    intervalo_km: Mapped[int | None] = mapped_column(Integer)

    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<CatalogoServicio {self.codigo} - {self.nombre}>"