import logging
import platform
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlmodel import Session

from musica_api.config import get_settings
from musica_api.database import create_db_and_tables, get_session
from musica_api.logging_config import configurar_logging
from musica_api.routers import canciones, favoritos, usuarios

settings = get_settings()

configurar_logging(settings.log_level, settings.log_file)
logger = logging.getLogger("musica_api.main")

# Momento en que arrancó la aplicación (para calcular el uptime)
HORA_INICIO = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la aplicación.
    """
    # Startup: Crear tablas en la base de datos
    create_db_and_tables()
    logger.info(
        "Aplicación iniciada: %s v%s (entorno=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    yield

    # Shutdown: Limpiar recursos si es necesario
    logger.info("Cerrando aplicación...")


# Crear la instancia de FastAPI con metadatos apropiados
# Incluir: title, description, version, contact, license_info
app = FastAPI(
    title=settings.app_name,
    description="API RESTful para gestionar usuarios, canciones y favoritos",
    version=settings.app_version,
    lifespan=lifespan,
    contact={
        "name": "MIGUEL ANGEL FERNANDEZ",
        "email": "migue2801224@gmail.com",
        "url": "https://github.com/MiguelAngel0-4/lpa2-taller3",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)


# Configurar CORS para permitir solicitudes desde diferentes orígenes
# Esto es importante para desarrollo con frontend separado
app.add_middleware(
    CORSMiddleware,
    # En producción, especificar orígenes permitidos en CORS_ORIGINS del .env
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Permite que un frontend lea estos encabezados personalizados
    expose_headers=["X-Total-Count", "X-Process-Time"],
)


# Incluir los routers de usuarios, canciones y favoritos
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(canciones.router, prefix="/api/canciones", tags=["Canciones"])
app.include_router(favoritos.router, prefix="/api/favoritos", tags=["Favoritos"])


# Crear un endpoint raíz que retorne información básica de la API
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    Retorna información básica y enlaces a la documentación.
    """
    return {
        "nombre": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.environment,
        "documentacion": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "usuarios": "/api/usuarios",
            "canciones": "/api/canciones",
            "favoritos": "/api/favoritos",
        },
    }


# Crear un endpoint de health check para monitoreo
@app.get("/health", tags=["Health"])
def health_check(session: Session = Depends(get_session)):
    """
    Health check endpoint para verificar el estado de la API.
    Útil para sistemas de monitoreo y orquestación.
    """
    try:
        session.exec(text("SELECT 1"))
        estado_db = "conectada"
    except Exception as error:
        logger.error("Health check: fallo de conexión a la base de datos: %s", error)
        estado_db = f"error: {error}"

    return {
        "status": "healthy" if estado_db == "conectada" else "unhealthy",
        "base_de_datos": estado_db,
        "sistema": {
            "uptime_segundos": round(time.time() - HORA_INICIO, 2),
            "python": platform.python_version(),
            "sistema_operativo": platform.system(),
        },
    }


# Middleware para logging de requests
@app.middleware("http")
async def registrar_peticiones(request: Request, call_next):
    """
    Registra cada petición con su método, ruta, código de estado y duración.
    También agrega la duración en el encabezado X-Process-Time.
    """
    inicio = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        # La traza completa la registra manejar_error_inesperado;
        # aquí solo se deja constancia de la petición y su duración.
        duracion_ms = (time.perf_counter() - inicio) * 1000
        logger.error(
            "%s %s -> 500 (%.2f ms)", request.method, request.url.path, duracion_ms
        )
        raise

    duracion_ms = (time.perf_counter() - inicio) * 1000
    response.headers["X-Process-Time"] = f"{duracion_ms:.2f}ms"

    # El nivel del log depende del resultado: 5xx = ERROR, 4xx = WARNING
    if response.status_code >= 500:
        nivel = logging.ERROR
    elif response.status_code >= 400:
        nivel = logging.WARNING
    else:
        nivel = logging.INFO

    logger.log(
        nivel,
        "%s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duracion_ms,
    )
    return response


# Manejadores de errores personalizados
@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(request: Request, exc: RequestValidationError):
    """Registra los datos inválidos y responde con el formato estándar 422."""
    campos = [".".join(str(parte) for parte in error["loc"]) for error in exc.errors()]
    logger.warning(
        "Validación fallida en %s %s: campos=%s",
        request.method,
        request.url.path,
        campos,
    )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, exc: Exception):
    """
    Captura cualquier error no controlado: lo registra con su traza completa
    y responde un 500 genérico, sin exponer detalles internos al cliente.
    """
    logger.error(
        "Error inesperado en %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
