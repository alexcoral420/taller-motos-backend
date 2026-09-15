"""
Cliente de Wompi: encapsula toda la comunicación con la API de Wompi.

Aísla las llamadas HTTP para que el service no sepa de los detalles de Wompi.
Flujo de Nequi push:
  1. obtener_acceptance_token()  -> token de aceptación de términos.
  2. crear_transaccion_nequi()   -> dispara el push al celular del cliente.
  3. consultar_transaccion()     -> revisa si el cliente aprobó.

Los montos en Wompi van en CENTAVOS (un peso = 100). Ojo con eso.
"""

import httpx
import hashlib
from app.core.config import settings


class WompiError(Exception):
    """Error al comunicarse con Wompi."""


class WompiClient:
    def __init__(self):
        self.base_url = settings.WOMPI_URL
        self.public_key = settings.WOMPI_PUBLIC_KEY
        self.private_key = settings.WOMPI_PRIVATE_KEY

    def obtener_acceptance_token(self) -> str:
        """
        Trae el token de aceptación de términos, obligatorio para crear pagos.
        Se consulta con la llave pública en el endpoint del comercio.
        """
        url = f"{self.base_url}/merchants/{self.public_key}"
        try:
            resp = httpx.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return data["data"]["presigned_acceptance"]["acceptance_token"]
        except (httpx.HTTPError, KeyError) as e:
            raise WompiError(f"No se pudo obtener el acceptance_token: {e}")

    def crear_transaccion_nequi(
        self,
        *,
        monto_centavos: int,
        referencia: str,
        email_cliente: str,
        telefono_nequi: str,
        acceptance_token: str,
    ) -> dict:
        """
        Crea una transacción Nequi. Dispara la notificación push al celular
        del cliente para que apruebe. Devuelve los datos de la transacción
        (incluye su id y estado inicial PENDING).
        """
        url = f"{self.base_url}/transactions"
        headers = {"Authorization": f"Bearer {self.private_key}"}
                    # Firma de integridad: SHA-256 de (referencia + monto + moneda + llave).
        cadena = f"{referencia}{monto_centavos}COP{settings.WOMPI_INTEGRITY_KEY}"
        firma = hashlib.sha256(cadena.encode()).hexdigest()
        payload = {
            "amount_in_cents": monto_centavos,
            "currency": "COP",
            "customer_email": email_cliente,
            "reference": referencia,
            "acceptance_token": acceptance_token,
            "signature": firma,
            "payment_method": {
                "type": "NEQUI",
                "phone_number": telefono_nequi,
            },
        }
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code >= 400:
                # Wompi devuelve el detalle del error en el cuerpo.
                raise WompiError(f"Wompi rechazó la transacción: {resp.text}")
            return resp.json()["data"]
        except httpx.HTTPError as e:
            raise WompiError(f"No se pudo crear la transacción Nequi: {e}")

    def consultar_transaccion(self, transaccion_id: str) -> dict:
        """
        Consulta el estado de una transacción por su id.
        Estados posibles: PENDING, APPROVED, DECLINED, ERROR, VOIDED.
        """
        url = f"{self.base_url}/transactions/{transaccion_id}"
        try:
            resp = httpx.get(url, timeout=20)
            resp.raise_for_status()
            return resp.json()["data"]
        except (httpx.HTTPError, KeyError) as e:
            raise WompiError(f"No se pudo consultar la transacción: {e}")