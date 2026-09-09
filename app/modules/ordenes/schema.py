"""
Schemas del módulo de órdenes de trabajo.

Dos formularios de ENTRADA distintos según el tipo de orden:

  - OrdenInternaCreate : registro RÁPIDO. Placa + servicios. Nada más.
                         (moto del inventario de la compraventa)

  - OrdenExternaCreate : registro COMPLETO. Cliente + moto + servicios.
                         (moto de un cliente de la calle)

En ambos, cada servicio lleva el VALOR que escribe el técnico (negociable).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.ordenes.model import TipoOrden


# ===========================================================================
#  ENTRADA — ítems de servicio (común a ambos tipos)
# ===========================================================================
class ServicioItemCreate(BaseModel):
    # Qué servicio del catálogo es (por su código de negocio).
    codigo: str = Field(..., min_length=1, max_length=50)
    # Descripción libre opcional (si el técnico quiere anotar algo).
    descripcion: str | None = Field(default=None, max_length=200)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0, le=999)
    # VALOR COBRADO por unidad, lo escribe el técnico (negociable).
    valor_unitario: Decimal = Field(..., ge=0)


# ===========================================================================
#  ENTRADA — datos del cliente (solo órdenes externas)
# ===========================================================================
class ClienteOrdenCreate(BaseModel):
    nombres: str = Field(..., min_length=1, max_length=120)
    telefono: str | None = Field(default=None, max_length=30)


# ===========================================================================
#  ENTRADA — orden INTERNA (registro rápido)
# ===========================================================================
class OrdenInternaCreate(BaseModel):
    placa: str = Field(..., min_length=1, max_length=20)   # obligatoria
    sintoma: str | None = Field(default=None, max_length=500)
    observaciones: str | None = Field(default=None, max_length=500)
    servicios: list[ServicioItemCreate] = Field(..., min_length=1, max_length=50)


# ===========================================================================
#  ENTRADA — orden EXTERNA (registro completo)
# ===========================================================================
class OrdenExternaCreate(BaseModel):
    placa: str | None = Field(default=None, max_length=20)  # recomendada, no obligatoria
    modelo_moto: str | None = Field(default=None, max_length=120)
    cliente: ClienteOrdenCreate
    sintoma: str | None = Field(default=None, max_length=500)
    observaciones: str | None = Field(default=None, max_length=500)
    servicios: list[ServicioItemCreate] = Field(..., min_length=1, max_length=50)


# ===========================================================================
#  SALIDA
# ===========================================================================
class OtItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    descripcion: str
    cantidad: Decimal
    valor_unitario: Decimal
    subtotal: Decimal


class OrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    tipo: TipoOrden
    placa: str | None
    cliente_id: int | None
    tecnico_id: int | None
    sintoma: str | None
    diagnostico: str | None
    total_mano_obra: Decimal
    total_repuestos: Decimal
    total: Decimal
    observaciones: str | None
    created_at: datetime
    items: list[OtItemOut] = []