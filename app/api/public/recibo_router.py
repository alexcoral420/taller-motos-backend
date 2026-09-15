"""
Router PÚBLICO del recibo de servicio.

El cliente abre este enlace (compartido por WhatsApp) y ve su recibo, que
puede guardar como PDF desde el navegador. Protegido por el token opaco del
pago (no el id interno).

Ruta final (se monta bajo /api/public):
    GET /api/public/recibo/{token}
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.pagos.service import OrdenNoEncontrada, PagoService

router = APIRouter(prefix="/recibo", tags=["Recibo (público)"])

# --- Datos fijos del taller ---
TALLER_NOMBRE = "Taller Universal"
TALLER_DIRECCION = "Av 1 de Mayo #29c-35"
TALLER_TELEFONO = "3204951482"

METODOS_LABEL = {
    "efectivo": "Efectivo",
    "nequi": "Nequi",
    "daviplata": "Daviplata",
    "breve": "Breve",
}


def _fmt(valor) -> str:
    """Formatea un número como moneda colombiana."""
    try:
        return f"${float(valor):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "$0"


@router.get("/{token}", response_class=HTMLResponse)
def ver_recibo(token: str, db: Session = Depends(get_db)):
    service = PagoService(db)
    try:
        datos = service.datos_recibo(uuid.UUID(token))
    except (OrdenNoEncontrada, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recibo no encontrado"
        )

    pago = datos["pago"]
    orden = datos["orden"]
    tecnico = datos["tecnico"]
    cliente = datos["cliente"]
    items = datos["items"]

    fecha = pago.created_at.strftime("%d/%m/%Y %H:%M") if pago.created_at else ""
    metodo = METODOS_LABEL.get(pago.metodo.value, pago.metodo.value)
    tecnico_nombre = tecnico.nombre if tecnico else "—"
    cliente_nombre = cliente.nombres if cliente else "—"
    modelo = orden.observaciones if False else None  # placeholder, no usado

    # Filas de servicios
    filas = ""
    for it in items:
        filas += f"""
        <tr>
          <td>{it.descripcion}</td>
          <td class="der">{_fmt(it.subtotal)}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Recibo #{orden.numero} - {TALLER_NOMBRE}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, Arial, sans-serif;
      background: #f3f4f6; margin: 0; padding: 16px; color: #1f2937;
    }}
    .recibo {{
      max-width: 420px; margin: 0 auto; background: #fff;
      border-radius: 12px; padding: 24px; box-shadow: 0 1px 6px rgba(0,0,0,.08);
    }}
    .taller {{ text-align: center; border-bottom: 2px solid #111; padding-bottom: 12px; margin-bottom: 16px; }}
    .taller h1 {{ margin: 0; font-size: 20px; }}
    .taller p {{ margin: 2px 0; font-size: 13px; color: #6b7280; }}
    .meta {{ font-size: 13px; margin-bottom: 16px; }}
    .meta div {{ display: flex; justify-content: space-between; padding: 3px 0; }}
    .meta span:first-child {{ color: #6b7280; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 12px; }}
    th {{ text-align: left; border-bottom: 1px solid #e5e7eb; padding: 6px 0; color: #6b7280; }}
    td {{ padding: 6px 0; border-bottom: 1px solid #f3f4f6; }}
    .der {{ text-align: right; }}
    .total {{ display: flex; justify-content: space-between; font-weight: bold; font-size: 16px; padding: 12px 0; border-top: 2px solid #111; }}
    .pago {{ font-size: 13px; margin-top: 8px; }}
    .nota {{ margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center; line-height: 1.5; }}
    .gracias {{ text-align: center; font-weight: 600; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="recibo">
    <div class="taller">
      <h1>{TALLER_NOMBRE}</h1>
      <p>{TALLER_DIRECCION}</p>
      <p>Tel: {TALLER_TELEFONO}</p>
    </div>

    <div class="meta">
      <div><span>Recibo N°</span><span>#{orden.numero}</span></div>
      <div><span>Fecha</span><span>{fecha}</span></div>
      <div><span>Cliente</span><span>{cliente_nombre}</span></div>
      <div><span>Placa</span><span>{orden.placa or "—"}</span></div>
      <div><span>Atendido por</span><span>{tecnico_nombre}</span></div>
    </div>

    <table>
      <thead>
        <tr><th>Servicio</th><th class="der">Valor</th></tr>
      </thead>
      <tbody>{filas}
      </tbody>
    </table>

    <div class="total">
      <span>TOTAL</span><span>{_fmt(pago.monto)}</span>
    </div>

    <div class="pago">
      <div style="display:flex;justify-content:space-between;">
        <span style="color:#6b7280;">Método de pago</span><span>{metodo}</span>
      </div>
    </div>

    <p class="gracias">¡Gracias por confiar en nosotros!</p>

    <p class="nota">
      Recuerda que la garantía del servicio depende de que tengas este recibo
      como prueba. Te recomendamos darle en imprimir y descargar como PDF.
    </p>
  </div>
</body>
</html>"""

    return HTMLResponse(content=html)