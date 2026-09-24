"""
Repositorio del módulo de pagos.

Hereda el CRUD del BaseRepository y añade la búsqueda por token público
(para servir el recibo por su enlace) y la suma de cobros por método para
el reporte del admin.
"""

import uuid
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.pagos.model import EstadoPago, MetodoPago, Pago


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, db: Session):
        super().__init__(Pago, db)

    def por_token(self, token: uuid.UUID) -> Pago | None:
        """Busca un pago por su token público (para el recibo)."""
        return self.get_by(public_token=token)

    def por_orden(self, orden_id: int) -> Pago | None:
        """El pago de una orden (pago único, así que a lo sumo uno)."""
        return self.get_by(orden_id=orden_id)

    def cobrado_por_metodo(self, orden_ids: Sequence[int]) -> dict[MetodoPago, Decimal]:
        """
        Suma de los pagos confirmados de esas órdenes, agrupada por método.
        Los métodos sin cobros no aparecen en el diccionario.
        """
        if not orden_ids:
            return {}
        stmt = (
            select(Pago.metodo, func.coalesce(func.sum(Pago.monto), 0))
            .where(
                Pago.orden_id.in_(orden_ids),
                Pago.estado == EstadoPago.confirmado,
            )
            .group_by(Pago.metodo)
        )
        return {metodo: total for metodo, total in self.db.execute(stmt).all()}
