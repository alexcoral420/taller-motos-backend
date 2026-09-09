"""
Punto de entrada de la aplicación.

Aquí se crea LA ÚNICA instancia de FastAPI y se ensambla todo:
  - Metadatos y documentación automática (/docs, /redoc).
  - CORS: qué dominios pueden llamar a la API.
  - Rate limiting por IP para la capa pública (slowapi).
  - Montaje del árbol público bajo /api/public.
  - (Más adelante) montaje del árbol privado bajo /api/v1.

Levantar en local:
    uvicorn app.main:app --reload

Nota: NO creamos tablas desde aquí (nada de Base.metadata.create_all).
El esquema ya vive en Supabase; la app solo se conecta a él.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.public.router import public_router
from app.core.config import settings

# Importar todos los modelos para que SQLAlchemy registre las tablas y
# resuelva las llaves foráneas entre ellas al arrancar.
from app.modules.clientes.model import Cliente
from app.modules.catalogo.model import CatalogoServicio
from app.modules.cotizaciones.model import Cotizacion, CotizacionItem
from app.modules.contacto.model import MensajeContacto
from app.modules.usuarios.model import Usuario

# ----------------------------------------------------------------------------
#  Rate limiter (capa pública)
#  Identifica al visitante por su IP y aplica el límite de PUBLIC_RATE_LIMIT
#  como techo por defecto. Protege los formularios públicos contra spam/abuso.
# ----------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.PUBLIC_RATE_LIMIT],
)

# ----------------------------------------------------------------------------
#  Instancia de la aplicación
# ----------------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
)

# Registrar el limiter en la app y su manejador de "límite excedido" (429).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ----------------------------------------------------------------------------
#  CORS — solo los dominios declarados en el .env pueden llamar a la API.
#  (Por ahora combinamos ambas listas; al montar el árbol privado podremos
#   afinar reglas por separado si hace falta.)
# ----------------------------------------------------------------------------
allowed_origins = settings.public_cors_list + settings.private_cors_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
#  Endpoints de salud (útiles para Railway y para probar que la app vive)
# ----------------------------------------------------------------------------
@app.get("/", tags=["Salud"])
def raiz():
    return {"app": settings.PROJECT_NAME, "entorno": settings.ENVIRONMENT}


@app.get("/health", tags=["Salud"])
def health():
    return {"status": "ok"}


# ----------------------------------------------------------------------------
#  Montaje de routers
# ----------------------------------------------------------------------------
# Árbol PÚBLICO (sitio web): sin auth, con rate limit y CORS restringido.
app.include_router(public_router, prefix=settings.API_PUBLIC_PREFIX)

# Árbol PRIVADO (paneles internos): se monta cuando lo construyamos.
from app.api.private.router import private_router
app.include_router(private_router, prefix=settings.API_V1_PREFIX)