"""
Router de INTEGRACIÓN: endpoints para sistemas externos (la compraventa).

A diferencia del panel (JWT), estos endpoints se autentican con API Key
(header X-API-Key), validada por verificar_api_key. Pensados para consumo
máquina a máquina.

Se monta bajo /api/integracion (ver main.py).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.integracion.deps import verificar_api_key
from app.core.database import get_db
from app.modules.ordenes.schema import GastoInternoDetalle
from app.modules.ordenes.service import OrdenService

# La dependencia de API key se aplica a TODO el router.
router = APIRouter(
    prefix="/integracion",
    tags=["Integración (sistemas externos)"],
    dependencies=[Depends(verificar_api_key)],
)


@router.get("/gasto-por-placa/{placa}", response_model=GastoInternoDetalle)
def gasto_por_placa(placa: str, db: Session = Depends(get_db)):
    """
    Total + detalle de servicios internos de una placa.
    Consumido por el sistema de compraventa para conocer el costo de
    acondicionamiento de cada moto del inventario.
    """
    service = OrdenService(db)
    return service.gasto_interno_detalle(placa)