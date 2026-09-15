"""
Service del módulo de pagos (liquidación de órdenes).

Reglas clave:
  - Solo se liquidan órdenes EXTERNAS (las internas son gastos, no se cobran).
  - Solo el TÉCNICO DUEÑO de la orden puede liquidarla (no manipulable).
  - Una orden solo se liquida UNA vez (pago único).
  - Al liquidar: crea el pago (manual/confirmado) y pasa la orden a 'liquidada'.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.ordenes.model import EstadoOrden, OrdenTrabajo, TipoOrden
from app.modules.ordenes.repository import OrdenRepository
from app.modules.pagos.model import EstadoPago, MetodoPago, OrigenPago, Pago
from app.modules.pagos.repository import PagoRepository
from app.modules.usuarios.model import Usuario


# ---------------------------------------------------------------------------
#  Excepciones de dominio
# ---------------------------------------------------------------------------
class PagoError(Exception):
    """Error base del dominio pagos."""


class OrdenNoEncontrada(PagoError):
    pass


class OrdenNoLiquidable(PagoError):
    """La orden no se puede liquidar (interna, ya liquidada, etc.)."""


class NoAutorizado(PagoError):
    """El técnico no es el dueño de la orden."""


# ---------------------------------------------------------------------------
#  Service
# ---------------------------------------------------------------------------
class PagoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PagoRepository(db)
        self.orden_repo = OrdenRepository(db)

    def liquidar(
        self, orden_id: int, metodo: MetodoPago, tecnico: Usuario
    ) -> Pago:
        orden = self.orden_repo.get(orden_id)
        if orden is None:
            raise OrdenNoEncontrada(f"No existe la orden id={orden_id}")

        # Regla 1: solo órdenes externas se cobran.
        if orden.tipo != TipoOrden.externo:
            raise OrdenNoLiquidable("Solo las órdenes externas se pueden liquidar")

        # Regla 2: solo el técnico dueño puede liquidar (no manipulable).
        if orden.tecnico_id != tecnico.id:
            raise NoAutorizado("Solo el técnico que registró la orden puede liquidarla")

        # Regla 3: no liquidar dos veces.
        if orden.estado == EstadoOrden.liquidada:
            raise OrdenNoLiquidable("La orden ya está liquidada")

        # Crear el pago (manual/confirmado) y cerrar la orden, de forma atómica.
        pago = Pago(
            orden_id=orden.id,
            tecnico_id=tecnico.id,
            monto=orden.total,
            metodo=metodo,
            estado=EstadoPago.confirmado,
            origen=OrigenPago.manual,
        )
        self.db.add(pago)
        orden.estado = EstadoOrden.liquidada  # cambia el estado en la misma transacción

        self.db.commit()
        self.db.refresh(pago)
        return pago

    def obtener_por_token(self, token) -> Pago:
        pago = self.repo.por_token(token)
        if pago is None:
            raise OrdenNoEncontrada("Recibo no encontrado")
        return pago

    def datos_recibo(self, token) -> dict:
        """Reúne todos los datos necesarios para el recibo, por su token."""
        pago = self.repo.por_token(token)
        if pago is None:
            raise OrdenNoEncontrada("Recibo no encontrado")

        orden = self.orden_repo.get(pago.orden_id)

        # Nombre del técnico que cobró.
        from app.modules.usuarios.repository import UsuarioRepository
        tecnico = UsuarioRepository(self.db).get(pago.tecnico_id) if pago.tecnico_id else None

        # Nombre del cliente (si la orden es externa y tiene cliente).
        cliente = None
        if orden and orden.cliente_id:
            from app.modules.clientes.model import Cliente
            cliente = self.db.get(Cliente, orden.cliente_id)

        return {
            "pago": pago,
            "orden": orden,
            "tecnico": tecnico,
            "cliente": cliente,
            "items": orden.items if orden else [],
        }