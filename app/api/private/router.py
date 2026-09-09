"""
Agregador de la capa PRIVADA.

Reúne todos los routers privados en un único 'private_router' que main.py
monta bajo el prefijo /api/v1. Cada nuevo router privado se registra aquí.

Todo lo que cuelga de este agregador es el panel interno: exige token JWT
(vía las dependencias de deps.py en cada router).
"""

from fastapi import APIRouter

from app.api.private import auth_router
# A medida que los construyamos, se agregan aquí:
from app.api.private import usuarios_router
# from app.api.private import cotizaciones_router
# from app.api.private import catalogo_router

private_router = APIRouter()

private_router.include_router(auth_router.router)
private_router.include_router(usuarios_router.router)
# private_router.include_router(cotizaciones_router.router)
# private_router.include_router(catalogo_router.router)