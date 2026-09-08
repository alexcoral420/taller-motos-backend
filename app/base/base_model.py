"""
Base declarativa y mixins reutilizables para todos los modelos.

- Base           : la clase declarativa de la que heredan TODOS los modelos.
- PKMixin        : llave primaria 'id' (bigint), generada por la base.
- TimestampMixin : columnas created_at + updated_at.
- CreatedAtMixin : solo created_at (para tablas de bitácora/junction que no
                   se actualizan, p.ej. ot_items, ot_historial_estado).

Cada modelo declara SU PROPIO __tablename__ para calzar exactamente con los
nombres del esquema SQL ya creado en Supabase (usuarios, clientes, etc.).

Ejemplo de uso (en modules/usuarios/model.py):
    from app.base.base_model import Base, PKMixin, TimestampMixin

    class Usuario(Base, PKMixin, TimestampMixin):
        __tablename__ = "usuarios"
        nombre: Mapped[str] = mapped_column(Text, nullable=False)
        ...
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase declarativa raíz. Todos los modelos heredan de aquí."""
    pass


class PKMixin:
    """Llave primaria entera, generada por la base (IDENTITY en el esquema)."""
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,   # la genera Postgres; no la enviamos en el INSERT
    )


class CreatedAtMixin:
    """Solo marca de creación (tablas que no se modifican después)."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    """Marca de creación + actualización automática."""
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),   # se refresca al hacer UPDATE desde el ORM;
                               # la base además tiene su propio trigger.
        nullable=False,
    )