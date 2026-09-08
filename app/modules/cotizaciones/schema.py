"""
Schemas (Pydantic v2) del módulo de cotizaciones.

ENTRADA (pública): la valida Pydantic ANTES de que el código la toque.
Como viene de internet, endurecemos: campos obligatorios, largos máximos,
email con formato válido, cantidades positivas. Si algo no cumple, FastAPI
responde 422 automáticamente y el request ni llega al service.

SALIDA:
  - CotizacionCreatedOut : lo que respondemos al público tras crear. Solo el
    token opaco y el estado. NADA de id interno.
  - CotizacionOut / ItemOut : vista completa para el panel del administrador.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.cotizaciones.model import EstadoCotizacion


# ===========================================================================
#  ENTRADA (formulario público)
# ===========================================================================
class CotizacionItemCreate(BaseModel):
    # El público referencia el servicio por su CÓDIGO de negocio, no por id.
    codigo: str = Field(..., min_length=1, max_length=50)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0, le=999)


class CotizacionCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    telefono: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    modelo_moto: str | None = Field(default=None, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)

    # Servicios seleccionados del catálogo (puede venir vacío).
    items: list[CotizacionItemCreate] = Field(default_factory=list, max_length=50)

    # Consentimiento de contacto (habeas data).
    acepta_publicidad: bool = False


# ===========================================================================
#  SALIDA PÚBLICA (respuesta al enviar el formulario)
# ===========================================================================
class CotizacionCreatedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_token: uuid.UUID
    estado: EstadoCotizacion


# ===========================================================================
#  SALIDA INTERNA (panel del administrador)
# ===========================================================================
class CotizacionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    catalogo_servicio_id: int
    cantidad: Decimal
    precio_referencia: Decimal


class CotizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_token: uuid.UUID
    nombre: str
    telefono: str | None
    email: str | None
    modelo_moto: str | None
    descripcion: str | None
    estado: EstadoCotizacion
    cliente_id: int | None
    acepta_publicidad: bool
    fecha_consentimiento: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[CotizacionItemOut] = []