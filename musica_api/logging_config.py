"""
Configuración del sistema de registro (logging).

Todos los loggers de la aplicación cuelgan de "musica_api"
(por ejemplo "musica_api.routers.usuarios"), así que basta con
configurar ese logger padre para que todos hereden el formato y destino.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def configurar_logging(nivel: str = "INFO", archivo: str = "") -> logging.Logger:
    """
    Configura el logger principal de la aplicación.

    Args:
        nivel: nivel mínimo a registrar (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        archivo: ruta del archivo de log. Si está vacío, solo se usa la consola.

    Returns:
        logging.Logger: el logger "musica_api" ya configurado.
    """
    logger = logging.getLogger("musica_api")
    logger.setLevel(nivel)

    # Evita handlers duplicados si el módulo se recarga (uvicorn --reload)
    if logger.handlers:
        return logger

    formato = logging.Formatter(FORMATO, FORMATO_FECHA)

    consola = logging.StreamHandler()
    consola.setFormatter(formato)
    logger.addHandler(consola)

    if archivo:
        Path(archivo).parent.mkdir(parents=True, exist_ok=True)
        # Rota el archivo al llegar a 1 MB y conserva los 3 anteriores
        archivo_handler = RotatingFileHandler(
            archivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        archivo_handler.setFormatter(formato)
        logger.addHandler(archivo_handler)

    return logger
