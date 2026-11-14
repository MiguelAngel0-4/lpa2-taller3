"""Endpoints para la gestión general de favoritos."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.models import Cancion, Favorito, FavoritoCreate, FavoritoRead, Usuario
from musica_api.pagination import Paginacion, paginar, parametros_paginacion

router = APIRouter()
logger = logging.getLogger(__name__)


def obtener_favorito_o_404(id_favorito: int, session: Session) -> Favorito:
    favorito = session.get(Favorito, id_favorito)
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    return favorito


@router.get("", response_model=list[FavoritoRead])
def listar_favoritos(
    response: Response,
    paginacion: Paginacion = Depends(parametros_paginacion),
    session: Session = Depends(get_session),
):
    consulta = select(Favorito).order_by(Favorito.id)
    return paginar(session, consulta, paginacion, response)


@router.post("", response_model=FavoritoRead, status_code=status.HTTP_201_CREATED)
def crear_favorito(datos: FavoritoCreate, session: Session = Depends(get_session)):
    if not session.get(Usuario, datos.id_usuario):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if not session.get(Cancion, datos.id_cancion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")

    existente = session.exec(
        select(Favorito).where(
            Favorito.id_usuario == datos.id_usuario,
            Favorito.id_cancion == datos.id_cancion,
        )
    ).first()
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "La canción ya es favorita")

    favorito = Favorito.model_validate(datos)
    session.add(favorito)
    session.commit()
    session.refresh(favorito)
    logger.info(
        "Favorito marcado: usuario=%s, cancion=%s", datos.id_usuario, datos.id_cancion
    )
    return favorito


@router.get("/{id}", response_model=FavoritoRead)
def obtener_favorito(id: int, session: Session = Depends(get_session)):
    return obtener_favorito_o_404(id, session)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_favorito(id: int, session: Session = Depends(get_session)):
    favorito = obtener_favorito_o_404(id, session)
    session.delete(favorito)
    session.commit()
    logger.info("Favorito eliminado: id=%s", id)
