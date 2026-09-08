"""
Repositorio del catálogo de servicios.

Hereda todo el CRUD genérico del BaseRepository (get, list, create,
update, delete, count, exists) y solo añade las consultas propias del
dominio del catálogo.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.catalogo.model import CatalogoServicio


class CatalogoRepository(BaseRepository[CatalogoServicio]):
    def __init__(self, db: Session):
        super().__init__(CatalogoServicio, db)

    # ------------------------------------------------------------------
    #  Consultas propias del catálogo
    # ------------------------------------------------------------------
    def por_codigo(self, codigo: str) -> CatalogoServicio | None:
        """Busca un servicio por su código de negocio (p.ej. 'SRV-ACEITE')."""
        return self.get_by(codigo=codigo)

    def listar_visibles_publico(self) -> Sequence[CatalogoServicio]:
        """
        Servicios que se muestran en la web pública:
        visibles Y activos. Esta es la ÚNICA consulta que alimenta la
        capa pública del catálogo.
        """
        stmt = (
            select(CatalogoServicio)
            .where(
                CatalogoServicio.visible_publico.is_(True),
                CatalogoServicio.activo.is_(True),
            )
            .order_by(CatalogoServicio.nombre)
        )
        return self.db.scalars(stmt).all()

    def por_codigos(self, codigos: list[str]) -> Sequence[CatalogoServicio]:
        """
        Trae varios servicios por una lista de códigos. Lo usará la
        cotización pública para validar y valorar los servicios que el
        cliente seleccionó en el formulario.
        """
        if not codigos:
            return []
        stmt = select(CatalogoServicio).where(
            CatalogoServicio.codigo.in_(codigos)
        )
        return self.db.scalars(stmt).all()