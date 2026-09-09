"""
Service del módulo de usuarios (reglas de negocio + autenticación).

Aquí se conectan las piezas de seguridad:
  - Al CREAR un usuario: se hashea la contraseña antes de guardarla.
  - Al hacer LOGIN: se verifica la contraseña y se emite el token JWT.

El service lanza excepciones de dominio; el router las traduce a HTTP.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.core.security import (
    crear_access_token,
    hash_password,
    verify_password,
)
from app.modules.usuarios.model import Usuario
from app.modules.usuarios.repository import UsuarioRepository
from app.modules.usuarios.schema import UsuarioCreate, UsuarioUpdate


# ---------------------------------------------------------------------------
#  Excepciones de dominio
# ---------------------------------------------------------------------------
class UsuarioError(Exception):
    """Error base del dominio usuarios."""


class UsuarioNoEncontrado(UsuarioError):
    pass


class EmailDuplicado(UsuarioError):
    pass


class CredencialesInvalidas(UsuarioError):
    """Email o contraseña incorrectos, o usuario inactivo."""


# ---------------------------------------------------------------------------
#  Service
# ---------------------------------------------------------------------------
class UsuarioService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    # ===================== AUTENTICACIÓN =====================
    def autenticar(self, email: str, password: str) -> tuple[str, Usuario]:
        """
        Verifica credenciales y, si son válidas, devuelve (token, usuario).
        Lanza CredencialesInvalidas si el email no existe, la contraseña no
        coincide, o el usuario está inactivo.
        """
        usuario = self.repo.por_email(email)

        # Mismo error para "no existe" y "contraseña mala": no revelamos
        # cuál de los dos falló (evita que un atacante descubra qué emails
        # están registrados).
        if usuario is None or not verify_password(password, usuario.password_hash):
            raise CredencialesInvalidas("Email o contraseña incorrectos")

        if not usuario.activo:
            raise CredencialesInvalidas("El usuario está inactivo")

        # Emitimos el token con el id como 'sub' y el rol como dato extra.
        token = crear_access_token(
            subject=usuario.id,
            extra={"rol": usuario.rol.value},
        )
        return token, usuario

    # ===================== GESTIÓN (admin) =====================
    def crear(self, data: UsuarioCreate) -> Usuario:
        if self.repo.exists(email=data.email):
            raise EmailDuplicado(f"Ya existe un usuario con email '{data.email}'")

        payload = data.model_dump(exclude={"password"})
        # La contraseña NO se guarda en claro: se hashea aquí.
        payload["password_hash"] = hash_password(data.password)
        return self.repo.create(payload)

    def listar(self, *, skip: int = 0, limit: int = 100) -> Sequence[Usuario]:
        return self.repo.list(skip=skip, limit=limit)

    def obtener(self, usuario_id: int) -> Usuario:
        obj = self.repo.get(usuario_id)
        if obj is None:
            raise UsuarioNoEncontrado(f"No existe el usuario id={usuario_id}")
        return obj

    def actualizar(self, usuario_id: int, data: UsuarioUpdate) -> Usuario:
        obj = self.obtener(usuario_id)
        cambios = data.model_dump(exclude_unset=True)

        # Si cambia el email, validar que el nuevo no exista.
        nuevo_email = cambios.get("email")
        if (
            nuevo_email is not None
            and nuevo_email != obj.email
            and self.repo.exists(email=nuevo_email)
        ):
            raise EmailDuplicado(f"Ya existe un usuario con email '{nuevo_email}'")

        # Si viene contraseña nueva, la hasheamos y quitamos el campo en claro.
        if "password" in cambios:
            password_plano = cambios.pop("password")
            if password_plano:
                cambios["password_hash"] = hash_password(password_plano)

        return self.repo.update(obj, cambios)