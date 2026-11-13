"""
Conexión a la base de datos.
Define el engine, la creación de tablas y la sesión que usan los endpoints.
"""

from sqlmodel import Session, SQLModel, create_engine

from musica_api.config import get_settings

settings = get_settings()

# SQLite por defecto solo permite usar una conexión desde el hilo que la creó.
# FastAPI atiende peticiones en varios hilos, por eso se desactiva esa restricción.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Crea todas las tablas definidas en los modelos (si no existen)."""
    # Importar los modelos registra las tablas en SQLModel.metadata
    from musica_api import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Dependencia de FastAPI: entrega una sesión por petición
    y la cierra automáticamente al terminar.
    """
    with Session(engine) as session:
        yield session
