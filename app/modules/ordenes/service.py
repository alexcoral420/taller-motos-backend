"""
Service del módulo de órdenes de trabajo (la lógica más rica del taller).

crear_interna:
  - Exige placa (vínculo con la compraventa).
  - Sin cliente. Es un COSTO de acondicionamiento de una moto del inventario.

crear_externa:
  - Crea/guarda el cliente en la tabla clientes (alimenta el CRM).
  - Es un INGRESO del taller.

En ambas:
  - Valida cada servicio contra el catálogo (por código).
  - Usa el VALOR que escribió el técnico (negociable), no el del catálogo.
  - Congela la comisión del técnico en cada ítem de mano de obra.
  - Calcula subtotales y totales.
  - Crea la orden + sus ítems de forma atómica (un solo commit).
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.catalogo.repository import CatalogoRepository
from app.modules.clientes.model import Cliente, OrigenCliente
from app.modules.ordenes.model import (
    OrdenTrabajo,
    OtItem,
    TipoItemOt,
    TipoOrden,
)
from app.modules.ordenes.repository import OrdenRepository
from app.modules.ordenes.schema import OrdenExternaCreate, OrdenInternaCreate
from app.modules.usuarios.model import Usuario


# ---------------------------------------------------------------------------
#  Excepciones de dominio
# ---------------------------------------------------------------------------
class OrdenError(Exception):
    """Error base del dominio órdenes."""


class ServicioInvalido(OrdenError):
    """Un servicio seleccionado no existe o no está activo."""


class OrdenNoEncontrada(OrdenError):
    pass


# ---------------------------------------------------------------------------
#  Service
# ---------------------------------------------------------------------------
class OrdenService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrdenRepository(db)
        self.catalogo_repo = CatalogoRepository(db)

    # ===================== ORDEN INTERNA =====================
    def crear_interna(
        self, data: OrdenInternaCreate, tecnico: Usuario
    ) -> OrdenTrabajo:
        items, total_mo = self._construir_items(data.servicios, tecnico)

        orden = OrdenTrabajo(
            tipo=TipoOrden.interno,
            placa=data.placa,
            tecnico_id=tecnico.id,
            sintoma=data.sintoma,
            observaciones=data.observaciones,
            total_mano_obra=total_mo,
            total_repuestos=Decimal("0"),
            total=total_mo,
        )
        for item in items:
            orden.items.append(item)

        return self._persistir(orden)

    # ===================== ORDEN EXTERNA =====================
    def crear_externa(
        self, data: OrdenExternaCreate, tecnico: Usuario
    ) -> OrdenTrabajo:
        items, total_mo = self._construir_items(data.servicios, tecnico)

        # Guardar el cliente en la tabla (alimenta el CRM).
        cliente = Cliente(
            nombres=data.cliente.nombres,
            telefono=data.cliente.telefono,
            origen=OrigenCliente.taller,
        )
        self.db.add(cliente)
        self.db.flush()   # obtiene cliente.id sin cerrar la transacción

        orden = OrdenTrabajo(
            tipo=TipoOrden.externo,
            placa=data.placa,
            cliente_id=cliente.id,
            tecnico_id=tecnico.id,
            sintoma=data.sintoma,
            observaciones=data.observaciones,
            total_mano_obra=total_mo,
            total_repuestos=Decimal("0"),
            total=total_mo,
        )
        for item in items:
            orden.items.append(item)

        return self._persistir(orden)

    # ===================== LECTURA (admin/técnico) =====================
    def listar(self, *, skip: int = 0, limit: int = 100) -> Sequence[OrdenTrabajo]:
        return self.repo.list(skip=skip, limit=limit)

    def obtener(self, orden_id: int) -> OrdenTrabajo:
        obj = self.repo.get(orden_id)
        if obj is None:
            raise OrdenNoEncontrada(f"No existe la orden id={orden_id}")
        return obj

    # ===================== HELPERS INTERNOS =====================
    def _construir_items(
        self, servicios, tecnico: Usuario
    ) -> tuple[list[OtItem], Decimal]:
        """
        Valida los servicios contra el catálogo, calcula subtotales con el
        valor que escribió el técnico y congela la comisión. Devuelve la
        lista de ítems y el total de mano de obra.
        """
        codigos = [s.codigo for s in servicios]
        encontrados = {c.codigo: c for c in self.catalogo_repo.por_codigos(codigos)}

        items: list[OtItem] = []
        total_mo = Decimal("0")
        comision_pct = tecnico.comision_pct_default or Decimal("0")

        for s in servicios:
            servicio = encontrados.get(s.codigo)
            if servicio is None or not servicio.activo:
                raise ServicioInvalido(
                    f"El servicio '{s.codigo}' no existe o no está activo"
                )

            subtotal = (s.valor_unitario * s.cantidad).quantize(Decimal("0.01"))
            comision_valor = (subtotal * comision_pct / Decimal("100")).quantize(
                Decimal("0.01")
            )

            items.append(
                OtItem(
                    tipo=TipoItemOt.mano_obra,
                    catalogo_servicio_id=servicio.id,
                    tecnico_id=tecnico.id,
                    descripcion=s.descripcion or servicio.nombre,
                    cantidad=s.cantidad,
                    valor_unitario=s.valor_unitario,   # valor del técnico
                    subtotal=subtotal,
                    comision_pct=comision_pct,          # congelada
                    comision_valor=comision_valor,      # congelada
                )
            )
            total_mo += subtotal

        return items, total_mo

    def _persistir(self, orden: OrdenTrabajo) -> OrdenTrabajo:
        """Guarda la orden y sus ítems en una sola transacción atómica."""
        self.db.add(orden)
        self.db.commit()
        self.db.refresh(orden)
        return orden