"""Configuración del sistema de registro (logs) en archivo."""

import logging
from pathlib import Path


def configurar_logger(nombre: str = "SoftwareFJ", archivo_log: str = "logs/sistema_fj.log") -> logging.Logger:
    """Crea y devuelve un logger que escribe en consola y en un archivo de texto."""
    ruta_log = Path(archivo_log)
    ruta_log.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(ruta_log, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formato)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formato)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger