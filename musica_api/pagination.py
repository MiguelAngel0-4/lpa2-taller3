"""
Utilidades de paginación para los endpoints que listan registros.

Se usa paginación por desplazamiento (offset/limit):
    GET /api/canciones?skip=20&limit=10  -> registros 21 a 30

El total de registros se devuelve en el encabezado HTTP X-Total-Count,
así el cuerpo de la respuesta sigue siendo una lista simple.
"""

from dataclasses import dataclass

from fastapi import Query, Response
from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

from musica_api.config import get_settings

settings = get_settings()


@dataclass
class Paginacion:
    """Parámetros de paginación recibidos en la URL."""

    skip: int
    limit: int


def parametros_paginacion(
    skip: int = Query(default=0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Número máximo de registros a devolver",
    ),
) -> Paginacion:
    """Dependencia de FastAPI que valida y agrupa skip y limit."""
    return Paginacion(skip=skip, limit=limit)


def paginar(
    session: Session,
    consulta: SelectOfScalar,
    paginacion: Paginacion,
    response: Response,
) -> list:
    """
    Aplica la paginación a una consulta y agrega el total al encabezado.

    Args:
        session: sesión de base de datos.
        consulta: consulta SELECT (con filtros y orden ya aplicados).
        paginacion: parámetros skip y limit.
        response: respuesta HTTP donde se escribe X-Total-Count.

    Returns:
        list: la "página" de resultados solicitada.
    """
    total = session.exec(select(func.count()).select_from(consulta.subquery())).one()
    response.headers["X-Total-Count"] = str(total)

    return session.exec(consulta.offset(paginacion.skip).limit(paginacion.limit)).all()
