"""Endpoints para la gestión de usuarios y sus favoritos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.models import (
    Cancion,
    Favorito,
    FavoritoRead,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)

router = APIRouter()


def obtener_usuario_o_404(id_usuario: int, session: Session) -> Usuario:
    usuario = session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return usuario


def verificar_correo_unico(correo: str, session: Session, excluir_id: int | None = None):
    existente = session.exec(select(Usuario).where(Usuario.correo == correo)).first()
    if existente and existente.id != excluir_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")


@router.get("", response_model=list[UsuarioRead])
def listar_usuarios(session: Session = Depends(get_session)):
    return session.exec(select(Usuario)).all()


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, session: Session = Depends(get_session)):
    verificar_correo_unico(datos.correo, session)
    usuario = Usuario.model_validate(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.get("/{id}", response_model=UsuarioRead)
def obtener_usuario(id: int, session: Session = Depends(get_session)):
    return obtener_usuario_o_404(id, session)


@router.put("/{id}", response_model=UsuarioRead)
def actualizar_usuario(
    id: int, datos: UsuarioUpdate, session: Session = Depends(get_session)
):
    usuario = obtener_usuario_o_404(id, session)
    cambios = datos.model_dump(exclude_unset=True)
    if "correo" in cambios:
        verificar_correo_unico(cambios["correo"], session, excluir_id=id)
    usuario.sqlmodel_update(cambios)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(id: int, session: Session = Depends(get_session)):
    usuario = obtener_usuario_o_404(id, session)
    session.delete(usuario)
    session.commit()


# ---------------------------------------------------------------------------
# Favoritos de un usuario
# ---------------------------------------------------------------------------

@router.get("/{id}/favoritos", response_model=list[FavoritoRead])
def listar_favoritos_usuario(id: int, session: Session = Depends(get_session)):
    obtener_usuario_o_404(id, session)
    return session.exec(select(Favorito).where(Favorito.id_usuario == id)).all()


@router.post(
    "/{id_usuario}/favoritos/{id_cancion}",
    response_model=FavoritoRead,
    status_code=status.HTTP_201_CREATED,
)
def marcar_favorito(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    obtener_usuario_o_404(id_usuario, session)
    if not session.get(Cancion, id_cancion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")

    existente = session.exec(
        select(Favorito).where(
            Favorito.id_usuario == id_usuario, Favorito.id_cancion == id_cancion
        )
    ).first()
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "La canción ya es favorita")

    favorito = Favorito(id_usuario=id_usuario, id_cancion=id_cancion)
    session.add(favorito)
    session.commit()
    session.refresh(favorito)
    return favorito


@router.delete(
    "/{id_usuario}/favoritos/{id_cancion}", status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_favorito_usuario(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    favorito = session.exec(
        select(Favorito).where(
            Favorito.id_usuario == id_usuario, Favorito.id_cancion == id_cancion
        )
    ).first()
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    session.delete(favorito)
    session.commit()
