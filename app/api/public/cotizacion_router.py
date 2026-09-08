"""
Router PÚBLICO de cotizaciones.

Expuesto a internet, sin autenticación. Recibe el formulario de cotización
del sitio web. Protegido por:
  - Validación estricta de Pydantic (schema CotizacionCreate).
  - Rate limiting por IP (configurado globalmente en main.py).
  - Captura de la IP de origen para auditoría anti-spam.

Ruta final (se monta bajo /api/public):
    POST /api/public/cotizaciones
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.cotizaciones.schema import (
    CotizacionCreate,
    CotizacionCreatedOut,
)
from app.modules.cotizaciones.service import CotizacionService, ServicioInvalido

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones (público)"])


def _ip_cliente(request: Request) -> str | None:
    """
    Obtiene la IP real del visitante. Detrás de un proxy (como en Railway),
    la IP viene en la cabecera X-Forwarded-For; si no, usamos la directa.
    """
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "",
    response_model=CotizacionCreatedOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_cotizacion_publica(
    data: CotizacionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Crea una cotización desde la web. Responde 201 con el token opaco y el
    estado. Si algún servicio seleccionado no es válido, responde 422.
    """
    service = CotizacionService(db)
    try:
        cotizacion = service.crear_publica(data, ip_origen=_ip_cliente(request))
    except ServicioInvalido as e:
        # Traducción excepción-de-dominio -> respuesta HTTP.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return cotizacion