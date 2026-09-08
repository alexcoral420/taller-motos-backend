"""
Service del módulo de cotizaciones (reglas de negocio del CRM).

Flujo público (crear_publica):
  1. Toma los CÓDIGOS de servicio que eligió el cliente.
  2. Los busca en el catálogo y valida que existan, estén activos y sean
     visibles al público (no se pueden cotizar servicios internos).
  3. CONGELA el precio de referencia de cada servicio en el momento de la
     solicitud (si mañana cambia el precio, este lead conserva el de hoy).
  4. Registra el consentimiento con su fecha (habeas data).
  5. Crea la cotización + sus ítems de forma atómica.

El service lanza excepciones de dominio; el router las traduce a HTTP.
"""

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.catalogo.repository import CatalogoRepository
from app.modules.cotizaciones.model import Cotizacion, EstadoCotizacion
from app.modules.cotizaciones.repository import CotizacionRepository
from app.modules.cotizaciones.schema import CotizacionCreate


# ---------------------------------------------------------------------------
#  Excepciones de dominio
# ---------------------------------------------------------------------------
class CotizacionError(Exception):
    """Error base del dominio cotizaciones."""


class ServicioInvalido(CotizacionError):
    """Uno de los servicios seleccionados no existe o no está disponible."""


class CotizacionNoEncontrada(CotizacionError):
    """No existe la cotización solicitada."""


# ---------------------------------------------------------------------------
#  Service
# ---------------------------------------------------------------------------
class CotizacionService:
    def __init__(self, db: Session):
        self.repo = CotizacionRepository(db)
        self.catalogo_repo = CatalogoRepository(db)

    # ===================== CAPA PÚBLICA =====================
    def crear_publica(
        self, data: CotizacionCreate, ip_origen: str | None = None
    ) -> Cotizacion:
        """Crea una cotización desde el formulario web."""
        items_data: list[dict] = []

        if data.items:
            codigos = [item.codigo for item in data.items]
            # Traemos de la base los servicios pedidos, en un solo query.
            servicios = self.catalogo_repo.por_codigos(codigos)
            # Mapa codigo -> servicio, solo con los disponibles al público.
            disponibles = {
                s.codigo: s
                for s in servicios
                if s.visible_publico and s.activo
            }

            for item in data.items:
                servicio = disponibles.get(item.codigo)
                if servicio is None:
                    raise ServicioInvalido(
                        f"El servicio '{item.codigo}' no existe o no está disponible"
                    )
                items_data.append(
                    {
                        "catalogo_servicio_id": servicio.id,
                        "cantidad": item.cantidad,
                        # Precio congelado al momento de cotizar:
                        "precio_referencia": servicio.precio_referencia,
                    }
                )

        # Datos de la cotización.
        cotizacion_data = {
            "nombre": data.nombre,
            "telefono": data.telefono,
            "email": str(data.email) if data.email else None,
            "modelo_moto": data.modelo_moto,
            "descripcion": data.descripcion,
            "acepta_publicidad": data.acepta_publicidad,
            # Solo guardamos fecha de consentimiento si el cliente aceptó.
            "fecha_consentimiento": (
                datetime.now(timezone.utc) if data.acepta_publicidad else None
            ),
            "ip_origen": ip_origen,
            "estado": EstadoCotizacion.nueva,
        }

        return self.repo.crear_con_items(cotizacion_data, items_data)

    # ===================== CAPA PRIVADA (admin) =====================
    def listar(
        self, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Cotizacion]:
        return self.repo.list(skip=skip, limit=limit)

    def listar_por_estado(
        self, estado: EstadoCotizacion, *, skip: int = 0, limit: int = 100
    ) -> Sequence[Cotizacion]:
        return self.repo.listar_por_estado(estado, skip=skip, limit=limit)

    def obtener(self, cotizacion_id: int) -> Cotizacion:
        obj = self.repo.get(cotizacion_id)
        if obj is None:
            raise CotizacionNoEncontrada(
                f"No existe la cotización id={cotizacion_id}"
            )
        return obj

    def cambiar_estado(
        self, cotizacion_id: int, nuevo_estado: EstadoCotizacion
    ) -> Cotizacion:
        obj = self.obtener(cotizacion_id)
        return self.repo.update(obj, {"estado": nuevo_estado})