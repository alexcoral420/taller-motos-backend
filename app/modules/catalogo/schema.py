"""
Schemas (Pydantic v2) del catálogo de servicios.

Separamos deliberadamente las salidas por audiencia:

  - CatalogoServicioPublic : lo ÚNICO que ve la web pública. No expone id
    interno, ni tipo, ni visible_publico, ni intervalos, ni activo. El
    servicio se referencia por 'codigo' (identificador de negocio), no por
    el id secuencial de la base.

  - CatalogoServicioOut : vista completa para el panel del administrador.

Entradas (Create/Update) solo las usa el panel privado; el público nunca
crea ni edita servicios.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalogo.model import TipoServicio


# ---------------------------------------------------------------------------
#  Entrada (solo panel privado / administrador)
# ---------------------------------------------------------------------------
class CatalogoServicioBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: str | None = None
    tipo: TipoServicio = TipoServicio.mano_obra
    precio_referencia: Decimal = Field(default=Decimal("0"), ge=0)
    visible_publico: bool = False
    intervalo_dias: int | None = Field(default=None, ge=0)
    intervalo_km: int | None = Field(default=None, ge=0)
    activo: bool = True


class CatalogoServicioCreate(CatalogoServicioBase):
    """Datos para crear un servicio (admin)."""
    pass


class CatalogoServicioUpdate(BaseModel):
    """Actualización parcial: todos los campos opcionales."""
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = None
    tipo: TipoServicio | None = None
    precio_referencia: Decimal | None = Field(default=None, ge=0)
    visible_publico: bool | None = None
    intervalo_dias: int | None = Field(default=None, ge=0)
    intervalo_km: int | None = Field(default=None, ge=0)
    activo: bool | None = None


# ---------------------------------------------------------------------------
#  Salida INTERNA (panel administrador) — vista completa
# ---------------------------------------------------------------------------
class CatalogoServicioOut(CatalogoServicioBase):
    model_config = ConfigDict(from_attributes=True)  # permite construir desde el ORM

    id: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
#  Salida PÚBLICA (web) — superficie mínima y segura
# ---------------------------------------------------------------------------
class CatalogoServicioPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    descripcion: str | None = None
    precio_referencia: Decimal