"""
Router PRIVADO de órdenes de trabajo.

Lo usan los técnicos (y el admin) autenticados. El técnico que crea la orden
se identifica por su token (get_current_user) y queda asociado a la orden
para su comisión — no hay que enviarlo en el cuerpo.

Rutas finales (se monta bajo /api/v1):
    POST /api/v1/ordenes/interna    -> registrar orden interna (rápida)
    POST /api/v1/ordenes/externa    -> registrar orden externa (completa)
    GET  /api/v1/ordenes            -> listar órdenes
    GET  /api/v1/ordenes/reporte    -> reporte filtrado + resumen (solo admin)
    GET  /api/v1/ordenes/{id}       -> ver una orden
    GET  /api/v1/ordenes/placa/{placa}/gasto-interno -> gasto interno por placa
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.private.deps import get_current_user, require_admin
from app.core.database import get_db
from app.modules.ordenes.model import EstadoOrden, TipoOrden
from app.modules.ordenes.schema import (
    OrdenExternaCreate,
    OrdenInternaCreate,
    OrdenOut,
)
from app.modules.ordenes.schema import (
    GastoInternoDetalle,
    OrdenExternaCreate,
    OrdenInternaCreate,
    OrdenOut,
    ReporteOrdenes,
)

from app.modules.ordenes.service import (
    OrdenNoEncontrada,
    OrdenService,
    RangoFechasInvalido,
    ServicioInvalido,
)
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/ordenes", tags=["Órdenes de trabajo"])


@router.post("/interna", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
def crear_orden_interna(
    data: OrdenInternaCreate,
    db: Session = Depends(get_db),
    tecnico: Usuario = Depends(get_current_user),   # el técnico autenticado
):
    """Registra una orden interna (moto del inventario). Registro rápido."""
    service = OrdenService(db)
    try:
        return service.crear_interna(data, tecnico)
    except ServicioInvalido as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/externa", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
def crear_orden_externa(
    data: OrdenExternaCreate,
    db: Session = Depends(get_db),
    tecnico: Usuario = Depends(get_current_user),
):
    """Registra una orden externa (moto de cliente). Guarda el cliente en el CRM."""
    service = OrdenService(db)
    try:
        return service.crear_externa(data, tecnico)
    except ServicioInvalido as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=list[OrdenOut])
def listar_ordenes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    service = OrdenService(db)
    return service.listar(usuario, skip=skip, limit=limit)


# Va antes de /{orden_id}: si no, "reporte" se intentaría leer como id.
@router.get("/reporte", response_model=ReporteOrdenes)
def reporte_ordenes(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    tecnico_id: int | None = None,
    tipo: TipoOrden | None = None,
    estado: EstadoOrden | None = None,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),   # solo admin
):
    """Reporte de órdenes con filtros opcionales, más su resumen por tipo."""
    service = OrdenService(db)
    try:
        return service.reporte(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tecnico_id=tecnico_id,
            tipo=tipo,
            estado=estado,
        )
    except RangoFechasInvalido as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/{orden_id}", response_model=OrdenOut)
def obtener_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """Devuelve una orden por su id."""
    service = OrdenService(db)
    try:
        return service.obtener(orden_id)
    except OrdenNoEncontrada as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/placa/{placa}/gasto-interno")
def gasto_interno_placa(
    placa: str,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """
    Total gastado en servicios INTERNOS para una placa.
    Este endpoint es el que el sistema de la compraventa consumirá por API.
    """
    service = OrdenService(db)
    total = service.repo.gasto_interno_por_placa(placa)
    return {"placa": placa, "gasto_interno": total}

@router.get("/placa/{placa}/gasto-interno-detalle", response_model=GastoInternoDetalle)
def gasto_interno_detalle(
    placa: str,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_user),
):
    """
    Total + detalle de los servicios internos de una placa.
    Endpoint pensado para el sistema de compraventa.
    """
    service = OrdenService(db)
    return service.gasto_interno_detalle(placa)