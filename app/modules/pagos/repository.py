"""
Repositorio del módulo de pagos.

Hereda el CRUD del BaseRepository y añade la búsqueda por token público
(para servir el recibo por su enlace).
"""

import uuid

from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.pagos.model import Pago


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, db: Session):
        super().__init__(Pago, db)

    def por_token(self, token: uuid.UUID) -> Pago | None:
        """Busca un pago por su token público (para el recibo)."""
        return self.get_by(public_token=token)

    def por_orden(self, orden_id: int) -> Pago | None:
        """El pago de una orden (pago único, así que a lo sumo uno)."""
        return self.get_by(orden_id=orden_id)