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
from app.modules.pagos.wompi import WompiClient, WompiError


# ---------------------------------------------------------------------------
#  Excepciones de dominio
# ---------------------------------------------------------------------------
class PagoError(Exception):
    """Error base del dominio pagos."""


class OrdenNoEncontrada(PagoError):
    pass


class OrdenNoLiquidable(PagoError):
    """La orden no se puede liquidar (interna, ya liquidada, etc.)."""

class ErrorPasarela(PagoError):
    """Falló la comunicación con la pasarela de pagos."""


class DatosClienteIncompletos(PagoError):
    """Falta el teléfono o email del cliente para el cobro digital."""


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

    def iniciar_cobro_nequi(self, orden_id: int, tecnico: Usuario) -> Pago:
        """
        Inicia un cobro Nequi para una orden externa. Crea el pago en estado
        PENDIENTE, dispara el push al celular del cliente vía Wompi, y guarda
        la referencia de la transacción para consultarla luego.
        """
        orden = self.orden_repo.get(orden_id)
        if orden is None:
            raise OrdenNoEncontrada(f"No existe la orden id={orden_id}")

        # Mismas reglas que la liquidación manual.
        if orden.tipo != TipoOrden.externo:
            raise OrdenNoLiquidable("Solo las órdenes externas se pueden cobrar")
        if orden.tecnico_id != tecnico.id:
            raise NoAutorizado("Solo el técnico que registró la orden puede cobrarla")
        if orden.estado == EstadoOrden.liquidada:
            raise OrdenNoLiquidable("La orden ya está liquidada")

        # Necesitamos el teléfono (Nequi) y un email del cliente.
        cliente = orden.cliente
        if cliente is None or not cliente.telefono:
            raise DatosClienteIncompletos(
                "El cliente no tiene teléfono registrado para el cobro Nequi"
            )
        telefono = "".join(c for c in cliente.telefono if c.isdigit())[-10:]
        email = cliente.email or "sincorreo@taller.com"

        # Referencia única para Wompi (nuestro identificador del cobro).
        import uuid as _uuid
        referencia = f"orden-{orden.id}-{_uuid.uuid4().hex[:8]}"

        # Crear el pago en estado PENDIENTE (aún no confirmado).
        pago = Pago(
            orden_id=orden.id,
            tecnico_id=tecnico.id,
            monto=orden.total,
            metodo=MetodoPago.nequi,
            estado=EstadoPago.pendiente,      # pendiente hasta que el cliente apruebe
            origen=OrigenPago.pasarela,
            referencia=referencia,
        )
        self.db.add(pago)
        self.db.flush()  # obtiene el id del pago sin cerrar la transacción

        # Llamar a Wompi: monto en CENTAVOS (pesos * 100).
        wompi = WompiClient()
        try:
            acceptance = wompi.obtener_acceptance_token()
            monto_centavos = int(orden.total * 100)
            data = wompi.crear_transaccion_nequi(
                monto_centavos=monto_centavos,
                referencia=referencia,
                email_cliente=email,
                telefono_nequi=telefono,
                acceptance_token=acceptance,
            )
        except WompiError as e:
            self.db.rollback()
            raise ErrorPasarela(str(e))

        # Guardar el id de transacción de Wompi en la referencia (para consultar).
        pago.referencia = data.get("id", referencia)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def confirmar_cobro_nequi(self, pago_id: int) -> Pago:
        """
        Consulta el estado de la transacción en Wompi y actualiza el pago.
        Si el cliente aprobó, marca el pago como confirmado y la orden como
        liquidada.
        """
        pago = self.repo.get(pago_id)
        if pago is None:
            raise OrdenNoEncontrada("Pago no encontrado")

        wompi = WompiClient()
        try:
            data = wompi.consultar_transaccion(pago.referencia)
        except WompiError as e:
            raise ErrorPasarela(str(e))

        estado_wompi = data.get("status")
        if estado_wompi == "APPROVED":
            pago.estado = EstadoPago.confirmado
            orden = self.orden_repo.get(pago.orden_id)
            if orden:
                orden.estado = EstadoOrden.liquidada
            self.db.commit()
            self.db.refresh(pago)
        elif estado_wompi in ("DECLINED", "ERROR", "VOIDED"):
            pago.estado = EstadoPago.fallido
            self.db.commit()
            self.db.refresh(pago)
        # Si sigue PENDING, no cambiamos nada (el cliente aún no aprueba).

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