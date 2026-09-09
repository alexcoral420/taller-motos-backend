"""
Repositorio del módulo de órdenes de trabajo.

Hereda el CRUD del BaseRepository y añade consultas propias, incluida la
que prepara el flujo hacia el sistema de la compraventa: el total gastado
en taller (servicios INTERNOS) por placa de moto.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.ordenes.model import OrdenTrabajo, TipoOrden


class OrdenRepository(BaseRepository[OrdenTrabajo]):
    def __init__(self, db: Session):
        super().__init__(OrdenTrabajo, db)

    def por_placa(
        self, placa: str, *, skip: int = 0, limit: int = 100
    ) -> Sequence[OrdenTrabajo]:
        """Todas las órdenes de una placa (internas y externas)."""
        stmt = (
            select(OrdenTrabajo)
            .where(OrdenTrabajo.placa == placa)
            .order_by(OrdenTrabajo.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def gasto_interno_por_placa(self, placa: str) -> Decimal:
        """
        Suma el total de todas las órdenes INTERNAS de una placa.
        Este es el dato que el sistema de la compraventa consultará por API
        para saber cuánto se gastó acondicionando esa moto.
        """
        stmt = select(func.coalesce(func.sum(OrdenTrabajo.total), 0)).where(
            OrdenTrabajo.placa == placa,
            OrdenTrabajo.tipo == TipoOrden.interno,
        )
        return self.db.scalar(stmt) or Decimal("0")

    def listar_por_tipo(
        self, tipo: TipoOrden, *, skip: int = 0, limit: int = 100
    ) -> Sequence[OrdenTrabajo]:
        """Órdenes filtradas por tipo (interno / externo)."""
        return self.list(skip=skip, limit=limit, tipo=tipo)