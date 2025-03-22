import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
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

# Ruta base donde se encuentran las recetas organizadas por categorías
BASE_DIR = "recetas"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja el comando /start del bot.
    Muestra el menú principal con las categorías de recetas.
    """
    user_id = update.effective_user.id
    logger.info(f"Usuario {user_id} ejecutó /start")
    
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text(WELCOME_MESSAGE)
    else:
        logger.warning(f"Usuario no autorizado {user_id} intentó iniciar el bot")
        await update.message.reply_text(UNAUTHORIZED_MESSAGE)
    
    # Obtener las categorías (subdirectorios en BASE_DIR)
    categorias = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]

    # Crear botones para cada categoría
    keyboard = [[InlineKeyboardButton(categoria.capitalize(), callback_data=f"categoria|{categoria}")]
                for categoria in categorias]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar mensaje con los botones al usuario
    await update.message.reply_text("Selecciona una categoría:", reply_markup=reply_markup)


async def mostrar_recetas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra las recetas disponibles en una categoría seleccionada.
    """
    query = update.callback_query
    await query.answer()

    # Obtener la categoría seleccionada del callback_data
    _, categoria = query.data.split("|")
    categoria_path = os.path.join(BASE_DIR, categoria)

    # Listar los archivos PDF en la categoría seleccionada
    recetas = [f for f in os.listdir(categoria_path) if f.endswith(".pdf")]

    # Crear botones para cada receta
    keyboard = [[InlineKeyboardButton(receta.replace(".pdf", "").capitalize(),
                                       callback_data=f"receta|{categoria}|{receta}")]
                for receta in recetas]
    
    # Agregar un botón para volver al menú principal
    keyboard.append([InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Editar el mensaje anterior para mostrar las recetas disponibles
    await query.edit_message_text(f"Recetas en la categoría *{categoria.capitalize()}*:", 
                                   reply_markup=reply_markup, parse_mode="Markdown")
    

async def enviar_receta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Envía el archivo PDF de la receta seleccionada.
    """
    query = update.callback_query
    await query.answer()

    # Obtener la categoría y el nombre del archivo PDF del callback_data
    _, categoria, receta_pdf = query.data.split("|")
    receta_path = os.path.join(BASE_DIR, categoria, receta_pdf)

    # Enviar el archivo PDF al usuario
    await context.bot.send_document(chat_id=query.message.chat_id, document=open(receta_path, "rb"))


async def volver_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Vuelve al menú principal desde cualquier parte del bot.
    """
    query = update.callback_query
    await query.answer()
    
    # Llamar a la función `start` para mostrar el menú principal nuevamente
    await start(update, context)


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

    # CallbackQueryHandlers para manejar interacciones con botones
    app.add_handler(CallbackQueryHandler(mostrar_recetas, pattern="^categoria\\|"))
    app.add_handler(CallbackQueryHandler(enviar_receta, pattern="^receta\\|"))
    app.add_handler(CallbackQueryHandler(volver_menu_principal, pattern="^volver$"))
    
    # Iniciar el bot en modo polling (consulta continua)
    logger.info("Bot iniciado y ejecutándose...")
    app.run_polling()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
