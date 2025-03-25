import os
from dotenv import load_dotenv
from typing import List
from log.logger import logger


# ---------------------------------------------------------------
# CARGAR VARIABLES DE ENTORNO
# ---------------------------------------------------------------
def load_environment_variables() -> None:
    """
    Carga las variables de entorno desde el archivo .env.
    Si no se cargan correctamente, lanza excepciones claras.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    try:
        load_dotenv()  # Cargar variables desde el archivo .env
    except Exception as e:
        logger.error(f"Error al cargar el archivo .env: {e}")
        raise RuntimeError("No se pudo cargar el archivo .env")

    # Validar las variables necesarias
    required_variables = ['TELEGRAM_TOKEN', 'USER_ID_R', 'USER_ID_C', 'USER_ID_E']
    missing_variables = [var for var in required_variables if not os.getenv(var)]

    if missing_variables:
        for var in missing_variables:
            logger.error(f"{var} no está definido en el archivo .env")
        raise ValueError(f"Faltan las siguientes variables en el archivo .env: {', '.join(missing_variables)}")

    logger.info("Variables de entorno cargadas correctamente.")


# ---------------------------------------------------------------
# VARIABLES DE CONFIGURACIÓN
# ---------------------------------------------------------------
# Cargar las variables de entorno
load_environment_variables()

# Token de Telegram para el bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# ID de usuarios
USER_ID_R = int(os.getenv('USER_ID_R'))
USER_ID_C = int(os.getenv('USER_ID_C'))
USER_ID_E = int(os.getenv('USER_ID_E'))


# ---------------------------------------------------------------
# USUARIOS AUTORIZADOS
# ---------------------------------------------------------------
AUTHORIZED_USERS: List[int] = [USER_ID_R, USER_ID_C, USER_ID_E]


# ---------------------------------------------------------------
# MENSAJES INFORMATIVOS
# ---------------------------------------------------------------
WELCOME_MESSAGE = "🍽 *Bienvenido/a al bot de recetas* 🍽"
UNAUTHORIZED_MESSAGE = "Lo siento, no tienes autorización para usar este bot."


# ---------------------------------------------------------------
# RUTA BASE DE ARCHIVOS
# ---------------------------------------------------------------
# Ruta base donde se encuentran las recetas organizadas por categorías
# BASE_DIR = "../recetas" <--- Para server
BASE_DIR = "recetas"

# Asegurar que la ruta BASE_DIR existe
if not os.path.isdir(BASE_DIR):
    logger.error(f"La ruta de recetas '{BASE_DIR}' no existe.")
    raise FileNotFoundError(f"La ruta de recetas '{BASE_DIR}' no existe.")

logger.info(f"Base de datos de recetas ubicada en: {BASE_DIR}")
