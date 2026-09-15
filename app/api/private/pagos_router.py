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
    DatosClienteIncompletos,
    ErrorPasarela,
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

class CobroNequiRequest(BaseModel):
    telefono: str

class CobroNequiOut(BaseModel):
    pago_id: int
    estado: str
    referencia: str
    mensaje: str


@router.post("/nequi/cobrar/{orden_id}", response_model=CobroNequiOut)
def cobrar_nequi(
    orden_id: int,
    data: CobroNequiRequest,
    db: Session = Depends(get_db),
    tecnico: Usuario = Depends(get_current_user),
):
    """
    Inicia un cobro Nequi: dispara el push al celular del cliente.
    El pago queda PENDIENTE hasta que el cliente apruebe en su app.
    """
    service = PagoService(db)
    try:
        pago = service.iniciar_cobro_nequi(orden_id, tecnico, telefono=data.telefono)
    except OrdenNoEncontrada as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NoAutorizado as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (OrdenNoLiquidable, DatosClienteIncompletos) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ErrorPasarela as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return CobroNequiOut(
        pago_id=pago.id,
        estado=pago.estado.value,
        referencia=pago.referencia,
        mensaje="Se envió la notificación a Nequi. El cliente debe aprobar en su app.",
    )


@router.get("/nequi/estado/{pago_id}", response_model=CobroNequiOut)
def estado_nequi(
    pago_id: int,
    db: Session = Depends(get_db),
    tecnico: Usuario = Depends(get_current_user),
):
    """
    Consulta si el cliente ya aprobó el cobro Nequi. Actualiza el pago y la
    orden si fue aprobado.
    """
    service = PagoService(db)
    try:
        pago = service.confirmar_cobro_nequi(pago_id)
    except OrdenNoEncontrada as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ErrorPasarela as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    mensajes = {
        "pendiente": "El cliente aún no ha aprobado el pago.",
        "confirmado": "¡Pago aprobado! La orden fue liquidada.",
        "fallido": "El pago fue rechazado o falló.",
    }
    return CobroNequiOut(
        pago_id=pago.id,
        estado=pago.estado.value,
        referencia=pago.referencia,
        mensaje=mensajes.get(pago.estado.value, ""),
    )