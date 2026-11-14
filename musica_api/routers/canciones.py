"""Endpoints para la gestión de canciones."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from musica_api.database import get_session
from musica_api.models import Cancion, CancionCreate, CancionRead, CancionUpdate

router = APIRouter()


def obtener_cancion_o_404(id_cancion: int, session: Session) -> Cancion:
    cancion = session.get(Cancion, id_cancion)
    if not cancion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    return cancion


@router.get("", response_model=list[CancionRead])
def listar_canciones(session: Session = Depends(get_session)):
    return session.exec(select(Cancion)).all()


@router.post("", response_model=CancionRead, status_code=status.HTTP_201_CREATED)
def crear_cancion(datos: CancionCreate, session: Session = Depends(get_session)):
    cancion = Cancion.model_validate(datos)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


# IMPORTANTE: /buscar debe declararse ANTES de /{id}.
# Si no, FastAPI intentaría interpretar "buscar" como un id numérico (error 422).
@router.get("/buscar", response_model=list[CancionRead])
def buscar_canciones(
    titulo: str | None = Query(default=None),
    artista: str | None = Query(default=None),
    genero: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    consulta = select(Cancion)
    if titulo:
        consulta = consulta.where(col(Cancion.titulo).ilike(f"%{titulo}%"))
    if artista:
        consulta = consulta.where(col(Cancion.artista).ilike(f"%{artista}%"))
    if genero:
        consulta = consulta.where(col(Cancion.genero).ilike(f"%{genero}%"))
    return session.exec(consulta).all()


@router.get("/{id}", response_model=CancionRead)
def obtener_cancion(id: int, session: Session = Depends(get_session)):
    return obtener_cancion_o_404(id, session)


@router.put("/{id}", response_model=CancionRead)
def actualizar_cancion(
    id: int, datos: CancionUpdate, session: Session = Depends(get_session)
):
    cancion = obtener_cancion_o_404(id, session)
    cancion.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cancion(id: int, session: Session = Depends(get_session)):
    cancion = obtener_cancion_o_404(id, session)
    session.delete(cancion)
    session.commit()
