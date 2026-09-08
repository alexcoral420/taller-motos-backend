"""
Schemas del módulo de contacto.

ENTRADA pública (MensajeContactoCreate): validada por Pydantic, endurecida
porque viene de internet.

SALIDA pública (MensajeRecibidoOut): solo una confirmación amable. No
devolvemos ni id ni datos internos.

SALIDA interna (MensajeContactoOut): vista completa para el panel admin.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ----------------------------- ENTRADA (público) -----------------------------
class MensajeContactoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    asunto: str | None = Field(default=None, max_length=150)
    mensaje: str = Field(..., min_length=1, max_length=2000)


# ----------------------------- SALIDA (público) ------------------------------
class MensajeRecibidoOut(BaseModel):
    recibido: bool = True
    mensaje: str = "Gracias por escribirnos. Te responderemos pronto."


# ----------------------------- SALIDA (interno) ------------------------------
class MensajeContactoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str | None
    telefono: str | None
    asunto: str | None
    mensaje: str
    atendido: bool
    created_at: datetime