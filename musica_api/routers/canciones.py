"""Endpoints para la gestión de canciones."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, col, select

from musica_api.database import get_session
from musica_api.models import Cancion, CancionCreate, CancionRead, CancionUpdate
from musica_api.pagination import Paginacion, paginar, parametros_paginacion

router = APIRouter()
logger = logging.getLogger(__name__)


def obtener_cancion_o_404(id_cancion: int, session: Session) -> Cancion:
    cancion = session.get(Cancion, id_cancion)
    if not cancion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    return cancion


@router.get("", response_model=list[CancionRead])
def listar_canciones(
    response: Response,
    paginacion: Paginacion = Depends(parametros_paginacion),
    session: Session = Depends(get_session),
):
    consulta = select(Cancion).order_by(Cancion.id)
    return paginar(session, consulta, paginacion, response)


@router.post("", response_model=CancionRead, status_code=status.HTTP_201_CREATED)
def crear_cancion(datos: CancionCreate, session: Session = Depends(get_session)):
    cancion = Cancion.model_validate(datos)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    logger.info("Canción creada: id=%s, titulo=%r", cancion.id, cancion.titulo)
    return cancion


# IMPORTANTE: /buscar debe declararse ANTES de /{id}.
# Si no, FastAPI intentaría interpretar "buscar" como un id numérico (error 422).
@router.get("/buscar", response_model=list[CancionRead])
def buscar_canciones(
    response: Response,
    titulo: str | None = Query(default=None),
    artista: str | None = Query(default=None),
    genero: str | None = Query(default=None),
    paginacion: Paginacion = Depends(parametros_paginacion),
    session: Session = Depends(get_session),
):
    consulta = select(Cancion).order_by(Cancion.id)
    if titulo:
        consulta = consulta.where(col(Cancion.titulo).ilike(f"%{titulo}%"))
    if artista:
        consulta = consulta.where(col(Cancion.artista).ilike(f"%{artista}%"))
    if genero:
        consulta = consulta.where(col(Cancion.genero).ilike(f"%{genero}%"))
    return paginar(session, consulta, paginacion, response)


@router.get("/{id}", response_model=CancionRead)
def obtener_cancion(id: int, session: Session = Depends(get_session)):
    return obtener_cancion_o_404(id, session)


@router.put("/{id}", response_model=CancionRead)
def actualizar_cancion(
    id: int, datos: CancionUpdate, session: Session = Depends(get_session)
):
    cancion = obtener_cancion_o_404(id, session)
    cambios = datos.model_dump(exclude_unset=True)
    cancion.sqlmodel_update(cambios)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    logger.info("Canción actualizada: id=%s, campos=%s", id, list(cambios))
    return cancion


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cancion(id: int, session: Session = Depends(get_session)):
    cancion = obtener_cancion_o_404(id, session)
    session.delete(cancion)
    session.commit()
    logger.info("Canción eliminada: id=%s", id)
