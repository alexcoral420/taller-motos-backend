"""
Router PRIVADO de pagos (liquidación de órdenes).

El técnico que liquida se identifica por su token (get_current_user). La
regla "solo el dueño puede liquidar" se valida en el service comparando ese
técnico con el que registró la orden.

Rutas finales (se monta bajo /api/v1):
    POST /api/v1/pagos/liquidar/{orden_id}   -> liquidar una orden externa
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.private.deps import get_current_user
from app.core.database import get_db
from app.modules.pagos.model import MetodoPago
from app.modules.pagos.service import (
    NoAutorizado,
    OrdenNoEncontrada,
    OrdenNoLiquidable,
    PagoService,
)
from app.modules.usuarios.model import Usuario

router = APIRouter(prefix="/pagos", tags=["Pagos / Liquidación"])


class LiquidarRequest(BaseModel):
    metodo: MetodoPago


class LiquidacionOut(BaseModel):
    orden_id: int
    monto: str
    metodo: MetodoPago
    recibo_token: str


@router.post("/liquidar/{orden_id}", response_model=LiquidacionOut)
def liquidar_orden(
    orden_id: int,
    data: LiquidarRequest,
    db: Session = Depends(get_db),
    tecnico: Usuario = Depends(get_current_user),
):
    """Liquida una orden externa con el método de pago indicado."""
    service = PagoService(db)
    try:
        pago = service.liquidar(orden_id, data.metodo, tecnico)
    except OrdenNoEncontrada as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NoAutorizado as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrdenNoLiquidable as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return LiquidacionOut(
        orden_id=pago.orden_id,
        monto=str(pago.monto),
        metodo=pago.metodo,
        recibo_token=str(pago.public_token),
    )