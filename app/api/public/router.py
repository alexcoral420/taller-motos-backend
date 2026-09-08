from fastapi import APIRouter

from app.api.public import catalogo_router
from app.api.public import cotizacion_router
from app.api.public import contacto_router

public_router = APIRouter()

public_router.include_router(catalogo_router.router)
public_router.include_router(cotizacion_router.router)
public_router.include_router(contacto_router.router)