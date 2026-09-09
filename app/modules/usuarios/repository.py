"""
Repositorio del módulo de usuarios.

Hereda el CRUD genérico del BaseRepository y añade la búsqueda por email,
que es la que necesita el login para encontrar al usuario que intenta entrar.
"""

from sqlalchemy.orm import Session

from app.base.base_repository import BaseRepository
from app.modules.usuarios.model import Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(Usuario, db)

    def por_email(self, email: str) -> Usuario | None:
        """Busca un usuario por su email (identificador de login)."""
        return self.get_by(email=email)