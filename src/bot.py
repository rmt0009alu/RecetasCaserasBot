import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from typing import List

# Configuración de logging
log_file = 'bot.log'
logging.basicConfig(
    filename=log_file,
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# Variables de entorno
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
USER_ID_R = os.getenv('USER_ID_R')

# Manejo de errores para las variables de entorno
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN no está definido en el archivo .env")
    raise ValueError("TELEGRAM_TOKEN no está definido en el archivo .env")

if not USER_ID_R:
    logger.error("USER_ID_R no está definido en el archivo .env")
    raise ValueError("USER_ID_R no está definido en el archivo .env")

# Lista de usuarios autorizados (convertir a entero)
AUTHORIZED_USERS: List[int] = [int(USER_ID_R)]

# Constantes para mensajes
WELCOME_MESSAGE = 'Bienvenido al buscador de recetas. ¿Qué receta buscas?'
UNAUTHORIZED_MESSAGE = 'Lo siento, no tienes autorización para usar este bot.'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja el comando /start del bot.
    """
    user_id = update.effective_user.id
    logger.info(f"Usuario {user_id} ejecutó /start")
    
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text(WELCOME_MESSAGE)
    else:
        logger.warning(f"Usuario no autorizado {user_id} intentó iniciar el bot")
        await update.message.reply_text(UNAUTHORIZED_MESSAGE)


# async def search_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """
#     Busca recetas basadas en la consulta del usuario.
#     """
#     user_id = update.effective_user.id
#     query = update.message.text.lower()
    
#     if user_id in AUTHORIZED_USERS:
#         logger.info(f"Usuario {user_id} busca recetas con: {query}")
#         # Aquí implementarías la lógica para buscar en tus archivos PDF o TEX.
#         await update.message.reply_text(f"Buscando recetas que contengan: {query}")
#     else:
#         logger.warning(f"Usuario no autorizado {user_id} intentó buscar recetas")
#         await update.message.reply_text(UNAUTHORIZED_MESSAGE)

def main() -> None:
    """
    Función principal para configurar y ejecutar el bot.
    """
    logger.info("Iniciando el bot...")
    
    # Crear la aplicación del bot con el token
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Configurar los manejadores de comandos y mensajes
    app.add_handler(CommandHandler("start", start))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_recipe))
    
    # Iniciar el bot en modo polling (consulta continua)
    logger.info("Bot iniciado y ejecutándose...")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
