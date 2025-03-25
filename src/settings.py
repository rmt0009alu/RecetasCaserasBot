import os
from dotenv import load_dotenv
from typing import List
from log.logger import logger


# ---------------------------------------------------------------
# VARIABLES DE ENTORNO
# ---------------------------------------------------------------
# Cargar variables de entorno desde .env
load_dotenv()

# Variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
USER_ID_R = os.getenv('USER_ID_R')
USER_ID_C = os.getenv('USER_ID_C')
USER_ID_E = os.getenv('USER_ID_E')
USER_ID_O = os.getenv('USER_ID_O')

# Manejo de errores para las variables de entorno
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN no definido en el archivo .env")
    raise ValueError("TELEGRAM_TOKEN no definido en el archivo .env")

if not USER_ID_R:
    logger.error("USER_ID no definido en el archivo .env")
    raise ValueError("USER_ID no definido en el archivo .env")


# ---------------------------------------------------------------
# USUARIOS AUTORIZADOS
# ---------------------------------------------------------------
# Lista de usuarios autorizados (convertir a entero)
AUTHORIZED_USERS: List[int] = [int(USER_ID_R), int(USER_ID_C), int(USER_ID_E), int(USER_ID_O)]


# ---------------------------------------------------------------
# MENSAJES INFORMATIVOS
# ---------------------------------------------------------------
# Constantes para mensajes
WELCOME_MESSAGE = f"\n🍽 *Bienvenido/a al bot de recetas* 🍽\n"
UNAUTHORIZED_MESSAGE = 'Lo siento, no tienes autorización para usar este bot.'


# ---------------------------------------------------------------
# RUTA BASE DE ARCHIVOS
# ---------------------------------------------------------------
# Ruta base donde se encuentran las recetas organizadas por categorías
BASE_DIR = "recetas"
