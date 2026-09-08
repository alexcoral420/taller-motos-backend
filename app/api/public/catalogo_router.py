"""
Router PÚBLICO del catálogo de servicios.

Expuesto a internet, sin autenticación. Solo LECTURA y solo de servicios
marcados como visibles. La superficie es mínima a propósito.

Se monta bajo el prefijo /api/public (ver main.py), así que las rutas
finales quedan como:
    GET /api/public/catalogo
    GET /api/public/catalogo/{codigo}
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.catalogo.schema import CatalogoServicioPublic
from app.modules.catalogo.service import CatalogoService, ServicioNoEncontrado

router = APIRouter(prefix="/catalogo", tags=["Catálogo (público)"])


@router.get("", response_model=list[CatalogoServicioPublic])
def listar_catalogo_publico(db: Session = Depends(get_db)):
    """
    Lista los servicios visibles y activos para mostrar en la web.
    El response_model garantiza que solo salgan los 4 campos públicos,
    aunque el service devuelva el objeto completo del ORM.
    """
    service = CatalogoService(db)
    return service.listar_visibles()


@router.get("/{codigo}", response_model=CatalogoServicioPublic)
def obtener_servicio_publico(codigo: str, db: Session = Depends(get_db)):
    """
    Detalle de un servicio por su código de negocio (p.ej. 'SRV-ACEITE').
    Devuelve 404 si no existe O si no está publicado, para no revelar
    la existencia de servicios internos.
    """
    service = CatalogoService(db)

    try:
        servicio = service.obtener_por_codigo(codigo)
    except ServicioNoEncontrado:
        # Traducción excepción-de-dominio -> respuesta HTTP (tarea del router)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        )

    # Guardia pública: un servicio no publicado se comporta como inexistente.
    if not (servicio.visible_publico and servicio.activo):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado",
        )

    return servicio