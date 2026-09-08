"""
Repositorio base genérico (capa de acceso a datos).

Es la ÚNICA capa que habla directamente con la base vía SQLAlchemy.
Todos los repositorios concretos heredan de aquí y solo añaden las
consultas específicas de su dominio.

Diseño en capas:
  router  ->  service  ->  repository  ->  base de datos
El repositorio NO lanza errores HTTP (404, etc.): devuelve None o listas
vacías. Traducir eso a respuestas HTTP es tarea del service/router.

Control de transacciones:
  Los métodos de escritura aceptan  commit=True  por defecto (operación
  simple de una sola entidad). Para operaciones que tocan varias tablas en
  UNA transacción atómica (p.ej. cerrar una OT + registrar historial +
  descontar inventario), el service llama con  commit=False  en cada paso y
  hace UN solo commit al final.

Ejemplo de repositorio concreto:
    class ClienteRepository(BaseRepository[Cliente]):
        def __init__(self, db: Session):
            super().__init__(Cliente, db)

        def por_documento(self, doc: str) -> Cliente | None:
            return self.get_by(numero_documento=doc)
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.base.base_model import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    # ------------------------------------------------------------------
    #  Lectura
    # ------------------------------------------------------------------
    def get(self, id_: int) -> ModelType | None:
        """Obtiene por llave primaria. None si no existe."""
        return self.db.get(self.model, id_)

    def get_by(self, **filters: Any) -> ModelType | None:
        """Primer registro que cumpla los filtros de igualdad dados."""
        stmt = select(self.model).filter_by(**filters)
        return self.db.scalars(stmt).first()

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Lista paginada, con filtros de igualdad opcionales."""
        stmt = select(self.model).filter_by(**filters)
        stmt = stmt.order_by(order_by if order_by is not None else self.model.id)
        stmt = stmt.offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def count(self, **filters: Any) -> int:
        """Cuenta registros que cumplen los filtros (para paginación)."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return self.db.scalar(stmt) or 0

    def exists(self, **filters: Any) -> bool:
        """True si existe al menos un registro con esos filtros."""
        stmt = select(self.model.id).filter_by(**filters).limit(1)
        return self.db.scalars(stmt).first() is not None

    # ------------------------------------------------------------------
    #  Escritura
    # ------------------------------------------------------------------
    def create(self, data: dict[str, Any], *, commit: bool = True) -> ModelType:
        obj = self.model(**data)
        self.db.add(obj)
        self._persist(commit)
        self.db.refresh(obj)   # trae id y defaults generados por la base
        return obj

    def update(
        self, db_obj: ModelType, data: dict[str, Any], *, commit: bool = True
    ) -> ModelType:
        for field, value in data.items():
            setattr(db_obj, field, value)
        self.db.add(db_obj)
        self._persist(commit)
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType, *, commit: bool = True) -> None:
        self.db.delete(db_obj)
        self._persist(commit)

    # ------------------------------------------------------------------
    #  Interno
    # ------------------------------------------------------------------
    def _persist(self, commit: bool) -> None:
        """Confirma la transacción, o solo hace flush si el service la controla."""
        if commit:
            self.db.commit()
        else:
            self.db.flush()   # envía el SQL pero deja la transacción abierta