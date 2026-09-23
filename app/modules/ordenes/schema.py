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
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.ordenes.model import EstadoOrden, TipoOrden


# ===========================================================================
#  ENTRADA — ítems de servicio (común a ambos tipos)
# ===========================================================================
class ServicioItemCreate(BaseModel):
    # Del catálogo: viene 'codigo'. Libre ("otro"): viene 'descripcion' sin código.
    codigo: str | None = Field(default=None, max_length=50)
    descripcion: str | None = Field(default=None, max_length=200)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0, le=999)
    valor_unitario: Decimal = Field(..., ge=0)

    @model_validator(mode="after")
    def validar_codigo_o_descripcion(self):
        # Debe traer al menos uno: código (catálogo) o descripción (libre).
        if not self.codigo and not self.descripcion:
            raise ValueError("El servicio debe tener código o descripción")
        return self


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
class ClienteEnOrden(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombres: str
    telefono: str | None = None

class OrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    tipo: TipoOrden
    placa: str | None
    cliente_id: int | None
    cliente: ClienteEnOrden | None = None
    tecnico_id: int | None
    sintoma: str | None
    diagnostico: str | None
    total_mano_obra: Decimal
    total_repuestos: Decimal
    total: Decimal
    observaciones: str | None
    created_at: datetime
    items: list[OtItemOut] = []
    estado: str

class OrdenInternaResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int
    total: Decimal
    sintoma: str | None
    created_at: datetime
    items: list[OtItemOut] = []


class GastoInternoDetalle(BaseModel):
    placa: str
    gasto_interno_total: Decimal
    cantidad_ordenes: int
    ordenes: list[OrdenInternaResumen] = []


# ===========================================================================
#  SALIDA — reporte de órdenes (solo admin)
# ===========================================================================
class ReporteOrdenFila(BaseModel):
    numero: int
    tipo: TipoOrden
    fecha: datetime
    tecnico: str | None          # nombre; None si el técnico ya no existe
    placa: str | None
    cliente: str | None          # nombre; None en las internas
    total: Decimal
    estado: EstadoOrden
    sintoma: str | None
    items: list[OtItemOut] = []  # servicios, para el detalle expandido


class ResumenPorTipo(BaseModel):
    cantidad: int = 0
    total: Decimal = Decimal("0")


class ReporteResumen(BaseModel):
    cantidad_ordenes: int
    total: Decimal
    interno: ResumenPorTipo
    externo: ResumenPorTipo


class ReporteOrdenes(BaseModel):
    ordenes: list[ReporteOrdenFila]
    resumen: ReporteResumen