"""
Conexión a la base de datos (Supabase / PostgreSQL).

Expone:
  - engine       : el motor de SQLAlchemy conectado a Supabase.
  - SessionLocal : fábrica de sesiones.
  - get_db()     : dependencia de FastAPI que entrega una sesión por request
                   y garantiza que se cierre al terminar.

Uso en un router:
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from app.core.database import get_db

    @router.get("/algo")
    def endpoint(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ----------------------------------------------------------------------------
#  Motor de conexión
#
#  Notas sobre Supabase + pooler:
#   - Usamos el CONNECTION POOLER de Supabase (puerto 6543, modo transaction).
#   - Con psycopg2 no hay problema de "prepared statements" contra pgbouncer
#     (ese problema aparece sobre todo con psycopg3), por eso elegimos
#     psycopg2-binary en requirements.
#   - pool_pre_ping=True: verifica que la conexión siga viva antes de usarla,
#     evitando errores por conexiones que el pooler cerró por inactividad.
#   - pool_recycle: recicla conexiones cada 5 min para no arrastrar sockets
#     muertos en un entorno serverless como Railway.
# ----------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,        # loguea el SQL emitido solo en modo debug
    future=True,
)

# ----------------------------------------------------------------------------
#  Fábrica de sesiones
#   - autoflush=False: controlamos nosotros cuándo se envían los cambios
#     (lo hace la capa de repositorio/servicio), no en cada consulta.
#   - expire_on_commit=False: tras un commit, los objetos siguen usables
#     (útil para devolverlos en la respuesta sin re-consultar).
# ----------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión por request y la cierra siempre al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()