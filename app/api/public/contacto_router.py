"""
Router PÚBLICO de contacto.

Recibe el formulario "escríbenos" del sitio web. Sin auth, protegido por
validación estricta y por el rate limiting global (main.py).

Ruta final (se monta bajo /api/public):
    POST /api/public/contacto
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.contacto.schema import (
    MensajeContactoCreate,
    MensajeRecibidoOut,
)
from app.modules.contacto.service import ContactoService

router = APIRouter(prefix="/contacto", tags=["Contacto (público)"])


def _ip_cliente(request: Request) -> str | None:
    """IP real del visitante (respeta X-Forwarded-For tras el proxy)."""
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "",
    response_model=MensajeRecibidoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_mensaje_publico(
    data: MensajeContactoCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Recibe un mensaje de contacto y confirma su recepción."""
    service = ContactoService(db)
    service.crear_publico(data, ip_origen=_ip_cliente(request))
    return MensajeRecibidoOut()