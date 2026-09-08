"""
Repositorio del módulo de contacto.

Hereda el CRUD del BaseRepository y añade una consulta para el panel admin:
listar los mensajes que aún no se han atendido.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.contacto.model import MensajeContacto


class ContactoRepository(BaseRepository[MensajeContacto]):
    def __init__(self, db: Session):
        super().__init__(MensajeContacto, db)

    def listar_no_atendidos(
        self, *, skip: int = 0, limit: int = 100
    ) -> Sequence[MensajeContacto]:
        """Mensajes pendientes de respuesta (para el panel del admin)."""
        return self.list(skip=skip, limit=limit, atendido=False)