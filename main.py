from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from musica_api.database import create_db_and_tables, get_session
from musica_api.routers import canciones, favoritos, usuarios

from musica_api.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la aplicación.
    """
    # Startup: Crear tablas en la base de datos
    create_db_and_tables()
    yield
    
    # Shutdown: Limpiar recursos si es necesario
    print("cerrando aplicación...")


# Crear la instancia de FastAPI con metadatos apropiados
# Incluir: title, description, version, contact, license_info
app = FastAPI(
    title="settings.app_name",
    description="API RESTful para gestionar usuarios, canciones y favoritos",
    version="settings.app_version",
    lifespan=lifespan,
    contact={
        "name": "MIGUEL ANGEL FERNANDEZ",
        "email": "migue2801224@gmail.com",
        "url": "https://github.com/MiguelAngel0-4/lpa2-taller3",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},

)


# Configurar CORS para permitir solicitudes desde diferentes orígenes
# Esto es importante para desarrollo con frontend separado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["settings.cors_origins"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: Incluir los routers de usuarios, canciones y favoritos
# Ejemplo:
# app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
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
async def health_check():
    """
    Health check endpoint para verificar el estado de la API.
    Útil para sistemas de monitoreo y orquestación.
    """
    return {
        "status": "healthy",
        # TODO: Agregar verificación de conexión a base de datos
        # TODO: Agregar información sobre el sistema (uptime, memoria, etc.)
    }


# TODO: Opcional - Agregar middleware para logging de requests


# TODO: Opcional - Agregar manejadores de errores personalizados


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        # TODO: Configurar el servidor uvicorn con los parámetros apropiados
    )


