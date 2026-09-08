"""
Repositorio del módulo de cotizaciones.

Hereda el CRUD genérico del BaseRepository y añade:
  - por_token          : buscar por el identificador opaco (public_token).
  - listar_por_estado  : filtrar leads por su estado (para el panel admin).
  - crear_con_items    : crear la cotización y sus ítems en UNA transacción.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.cotizaciones.model import (
    Cotizacion,
    CotizacionItem,
    EstadoCotizacion,
)


class CotizacionRepository(BaseRepository[Cotizacion]):
    def __init__(self, db: Session):
        super().__init__(Cotizacion, db)

    def por_token(self, token: uuid.UUID) -> Cotizacion | None:
        """Busca una cotización por su token público (no por id interno)."""
        return self.get_by(public_token=token)

    def listar_por_estado(
        self, estado: EstadoCotizacion, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Cotizacion]:
        """Leads en un estado dado (nueva, en_proceso, etc.)."""
        return self.list(skip=skip, limit=limit, estado=estado)

    def crear_con_items(
        self, data: dict, items: list[dict]
    ) -> Cotizacion:
        """
        Crea la cotización y todos sus ítems como una sola unidad atómica.
        Si algo falla, no queda una cotización a medias sin sus servicios.
        """
        cotizacion = Cotizacion(**data)
        for item in items:
            cotizacion.items.append(CotizacionItem(**item))

        self.db.add(cotizacion)
        self.db.commit()          # un solo commit para el padre y los hijos
        self.db.refresh(cotizacion)
        return cotizacion