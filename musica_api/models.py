"""
Modelos de datos de la API de Música.

Para cada entidad se usa el patrón:
- <Entidad>Base:   campos compartidos
- <Entidad>:       tabla en la base de datos (table=True)
- <Entidad>Create: datos que llegan al crear (validados con Pydantic)
- <Entidad>Read:   datos que se devuelven al cliente
- <Entidad>Update: datos opcionales para actualizar
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import field_validator
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from utils import validar_año, validar_correo


def ahora_utc() -> datetime:
    """Fecha y hora actual en UTC (con zona horaria, como exige SQLModel)."""
    return datetime.now(timezone.utc)


# =============================================================================
# USUARIO
# =============================================================================

class UsuarioBase(SQLModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str = Field(max_length=150, index=True, unique=True)


class Usuario(UsuarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_registro: datetime = Field(default_factory=ahora_utc)

    favoritos: list["Favorito"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class UsuarioCreate(UsuarioBase):
    @field_validator("correo")
    @classmethod
    def validar_formato_correo(cls, v: str) -> str:
        if not validar_correo(v):
            raise ValueError("El correo electrónico no tiene un formato válido")
        return v.lower()


class UsuarioRead(UsuarioBase):
    id: int
    fecha_registro: datetime


class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    correo: Optional[str] = Field(default=None, max_length=150)

    @field_validator("correo")
    @classmethod
    def validar_formato_correo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validar_correo(v):
            raise ValueError("El correo electrónico no tiene un formato válido")
        return v.lower() if v else v


# =============================================================================
# CANCIÓN
# =============================================================================

class CancionBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=200, index=True)
    artista: str = Field(min_length=1, max_length=150, index=True)
    album: Optional[str] = Field(default=None, max_length=200)
    duracion: int = Field(gt=0, description="Duración en segundos")
    año: int
    genero: str = Field(min_length=1, max_length=50, index=True)


class Cancion(CancionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=ahora_utc)

    favoritos: list["Favorito"] = Relationship(
        back_populates="cancion",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class CancionCreate(CancionBase):
    @field_validator("año")
    @classmethod
    def validar_año_lanzamiento(cls, v: int) -> int:
        if not validar_año(v):
            raise ValueError("El año debe estar entre 1900 y el año actual")
        return v


class CancionRead(CancionBase):
    id: int
    fecha_creacion: datetime


class CancionUpdate(SQLModel):
    titulo: Optional[str] = Field(default=None, min_length=1, max_length=200)
    artista: Optional[str] = Field(default=None, min_length=1, max_length=150)
    album: Optional[str] = Field(default=None, max_length=200)
    duracion: Optional[int] = Field(default=None, gt=0)
    año: Optional[int] = None
    genero: Optional[str] = Field(default=None, min_length=1, max_length=50)

    @field_validator("año")
    @classmethod
    def validar_año_lanzamiento(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not validar_año(v):
            raise ValueError("El año debe estar entre 1900 y el año actual")
        return v


# =============================================================================
# FAVORITO
# =============================================================================

class FavoritoBase(SQLModel):
    id_usuario: int = Field(foreign_key="usuario.id")
    id_cancion: int = Field(foreign_key="cancion.id")


class Favorito(FavoritoBase, table=True):
    # Un usuario no puede marcar la misma canción dos veces
    __table_args__ = (UniqueConstraint("id_usuario", "id_cancion"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_marcado: datetime = Field(default_factory=ahora_utc)

    usuario: Optional[Usuario] = Relationship(back_populates="favoritos")
    cancion: Optional[Cancion] = Relationship(back_populates="favoritos")


class FavoritoCreate(FavoritoBase):
    pass


class FavoritoRead(FavoritoBase):
    id: int
    fecha_marcado: datetime
