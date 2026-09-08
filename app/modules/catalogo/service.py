"""
Service del catálogo de servicios (capa de reglas de negocio).

Se sienta entre el router y el repositorio:
    router  ->  service  ->  repository  ->  base

Responsabilidades:
  - Aplicar reglas (código único, existencia, etc.).
  - Orquestar el repositorio.
  - Lanzar EXCEPCIONES DE DOMINIO (no errores HTTP). El router las traduce
    luego a 404/409/etc. Así el service no sabe nada de HTTP y se puede
    reutilizar desde la web pública, el panel privado o un script.

Devuelve objetos del ORM. Quién decide qué campos se exponen es el
'response_model' del router (público vs interno), que actúa como filtro
de salida garantizado.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.modules.catalogo.model import CatalogoServicio
from app.modules.catalogo.repository import CatalogoRepository
from app.modules.catalogo.schema import (
    CatalogoServicioCreate,
    CatalogoServicioUpdate,
)


# ---------------------------------------------------------------------------
#  Excepciones de dominio (más adelante las centralizamos en core/exceptions)
# ---------------------------------------------------------------------------
class CatalogoError(Exception):
    """Error base del dominio catálogo."""


class ServicioNoEncontrado(CatalogoError):
    """No existe el servicio solicitado."""


class CodigoDuplicado(CatalogoError):
    """Ya existe un servicio con ese código."""


# ---------------------------------------------------------------------------
#  Service
# ---------------------------------------------------------------------------
class CatalogoService:
    def __init__(self, db: Session):
        # El service construye su repositorio con la sesión recibida.
        self.repo = CatalogoRepository(db)

    # ===================== USADO POR LA CAPA PÚBLICA =====================
    def listar_visibles(self) -> Sequence[CatalogoServicio]:
        """Servicios visibles y activos para mostrar en la web pública."""
        return self.repo.listar_visibles_publico()

    # ===================== USADO POR LA CAPA PRIVADA =====================
    def listar(self, *, skip: int = 0, limit: int = 100) -> Sequence[CatalogoServicio]:
        """Lista completa (admin), paginada."""
        return self.repo.list(skip=skip, limit=limit)

    def obtener(self, servicio_id: int) -> CatalogoServicio:
        obj = self.repo.get(servicio_id)
        if obj is None:
            raise ServicioNoEncontrado(f"No existe el servicio id={servicio_id}")
        return obj

    def obtener_por_codigo(self, codigo: str) -> CatalogoServicio:
        obj = self.repo.por_codigo(codigo)
        if obj is None:
            raise ServicioNoEncontrado(f"No existe el servicio '{codigo}'")
        return obj

    def crear(self, data: CatalogoServicioCreate) -> CatalogoServicio:
        # Regla: el código debe ser único.
        if self.repo.exists(codigo=data.codigo):
            raise CodigoDuplicado(f"Ya existe un servicio con código '{data.codigo}'")
        return self.repo.create(data.model_dump())

    def actualizar(
        self, servicio_id: int, data: CatalogoServicioUpdate
    ) -> CatalogoServicio:
        obj = self.obtener(servicio_id)  # reutiliza la validación de existencia

        # exclude_unset: solo los campos que el cliente realmente envió.
        cambios = data.model_dump(exclude_unset=True)

        # Regla: si cambia el código, validar que el nuevo no exista ya.
        nuevo_codigo = cambios.get("codigo")
        if (
            nuevo_codigo is not None
            and nuevo_codigo != obj.codigo
            and self.repo.exists(codigo=nuevo_codigo)
        ):
            raise CodigoDuplicado(f"Ya existe un servicio con código '{nuevo_codigo}'")

        return self.repo.update(obj, cambios)

    def eliminar(self, servicio_id: int) -> None:
        obj = self.obtener(servicio_id)
        self.repo.delete(obj)