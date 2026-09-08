"""
Service del módulo de contacto (reglas de negocio).

Muy simple: crear el mensaje desde la web, y para el admin listar y marcar
como atendido. Lanza excepciones de dominio; el router las traduce a HTTP.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.contacto.model import MensajeContacto
from app.modules.contacto.repository import ContactoRepository
from app.modules.contacto.schema import MensajeContactoCreate


class ContactoError(Exception):
    """Error base del dominio contacto."""


class MensajeNoEncontrado(ContactoError):
    """No existe el mensaje solicitado."""


class ContactoService:
    def __init__(self, db: Session):
        self.repo = ContactoRepository(db)

    # ===================== CAPA PÚBLICA =====================
    def crear_publico(
        self, data: MensajeContactoCreate, ip_origen: str | None = None
    ) -> MensajeContacto:
        payload = data.model_dump()
        payload["email"] = str(data.email) if data.email else None
        payload["ip_origen"] = ip_origen
        return self.repo.create(payload)

    # ===================== CAPA PRIVADA (admin) =====================
    def listar(self, *, skip: int = 0, limit: int = 100) -> Sequence[MensajeContacto]:
        return self.repo.list(skip=skip, limit=limit)

    def listar_no_atendidos(
        self, *, skip: int = 0, limit: int = 100
    ) -> Sequence[MensajeContacto]:
        return self.repo.listar_no_atendidos(skip=skip, limit=limit)

    def marcar_atendido(self, mensaje_id: int) -> MensajeContacto:
        obj = self.repo.get(mensaje_id)
        if obj is None:
            raise MensajeNoEncontrado(f"No existe el mensaje id={mensaje_id}")
        return self.repo.update(obj, {"atendido": True})