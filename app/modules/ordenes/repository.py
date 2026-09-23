"""
Repositorio del módulo de órdenes de trabajo.

Hereda el CRUD del BaseRepository y añade consultas propias, incluida la
que prepara el flujo hacia el sistema de la compraventa: el total gastado
en taller (servicios INTERNOS) por placa de moto.
"""

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session, selectinload

from app.base.base_repository import BaseRepository
from app.modules.ordenes.model import EstadoOrden, OrdenTrabajo, TipoOrden
from app.modules.usuarios.model import Usuario

# Hora de Colombia (UTC-5, sin horario de verano). Los días del reporte se
# cortan a medianoche local, no a medianoche UTC.
ZONA_TALLER = timezone(timedelta(hours=-5))


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

    def listar_para_usuario(
        self, usuario, *, skip: int = 0, limit: int = 100
    ):
      
        from app.modules.usuarios.model import RolUsuario

        stmt = select(OrdenTrabajo)

        # El técnico solo ve las suyas; el admin ve todas.
        if usuario.rol != RolUsuario.administrador:
            stmt = stmt.where(OrdenTrabajo.tecnico_id == usuario.id)

        stmt = stmt.order_by(OrdenTrabajo.created_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def reporte(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        tecnico_id: int | None = None,
        tipo: TipoOrden | None = None,
        estado: EstadoOrden | None = None,
    ) -> Sequence[Row[tuple[OrdenTrabajo, str | None]]]:
        """
        Órdenes para el reporte del admin, junto al nombre del técnico.
        Solo aplica los filtros que vienen (None = sin filtrar). El rango de
        fechas es inclusivo en ambos extremos. Más recientes primero.
        """
        stmt = (
            select(OrdenTrabajo, Usuario.nombre)
            .outerjoin(Usuario, Usuario.id == OrdenTrabajo.tecnico_id)
            # Los ítems en una sola consulta extra (evita una por orden).
            .options(selectinload(OrdenTrabajo.items))
        )

        if fecha_desde is not None:
            inicio = datetime.combine(fecha_desde, time.min, tzinfo=ZONA_TALLER)
            stmt = stmt.where(OrdenTrabajo.created_at >= inicio)
        if fecha_hasta is not None:
            # Inclusivo: todo el día 'fecha_hasta', hasta antes de la medianoche siguiente.
            fin = datetime.combine(
                fecha_hasta + timedelta(days=1), time.min, tzinfo=ZONA_TALLER
            )
            stmt = stmt.where(OrdenTrabajo.created_at < fin)
        if tecnico_id is not None:
            stmt = stmt.where(OrdenTrabajo.tecnico_id == tecnico_id)
        if tipo is not None:
            stmt = stmt.where(OrdenTrabajo.tipo == tipo)
        if estado is not None:
            stmt = stmt.where(OrdenTrabajo.estado == estado)

        stmt = stmt.order_by(OrdenTrabajo.created_at.desc())
        return self.db.execute(stmt).all()