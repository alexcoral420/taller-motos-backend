"""
Modelo del módulo de contacto (tabla: mensajes_contacto).

Mensajes que envían los visitantes desde el formulario "escríbenos" de la
web pública. Es una bitácora simple: se crea y se marca como atendido, pero
no se "actualiza" en el sentido habitual, por eso usa solo CreatedAtMixin.
"""

from sqlalchemy import Boolean, Text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_model import Base, CreatedAtMixin, PKMixin


class MensajeContacto(Base, PKMixin, CreatedAtMixin):
    __tablename__ = "mensajes_contacto"

    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(Text)
    asunto: Mapped[str | None] = mapped_column(Text)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)

    # El admin lo marca cuando ya respondió.
    atendido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    ip_origen: Mapped[str | None] = mapped_column(INET)

    def __repr__(self) -> str:
        return f"<MensajeContacto {self.nombre} - atendido={self.atendido}>"