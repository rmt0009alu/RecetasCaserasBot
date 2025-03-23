import sys
import os
# Agregar el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from settings import *
from log.logger import logger


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja el comando /start del bot y muestra el menú principal con las categorías de recetas.

    Parameters
    ----------
    update : Update
        Objeto de actualización de Telegram.
    context : ContextTypes.DEFAULT_TYPE
        Contexto de ejecución del bot.

    Returns
    -------
    None
    """
    user_id = update.effective_user.id
    logger.info(f"Usuario {user_id} ejecutó /start")

    # Limpiar el chat: eliminar el mensaje anterior si existe
    if update.message:
        try:
            await update.message.delete()
        except Exception as e:
            logger.error(f"No se pudo eliminar el mensaje anterior: {e}")

    if user_id in AUTHORIZED_USERS:
        # Verificamos si update.message está disponible, si no, usamos query.message
        if update.message:
            await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
        else:
            # Si update.message es None, se puede usar query.message (cuando el comando es desde un callback)
            # pero prefiero que no muestre ningún mensaje, porque este caso se da cuando el usuario 'vuelve'
            # al menú principal:
            # await update.callback_query.message.reply_text(f"🍽 *EPA* 🍽\n\n¿Qué receta buscas?", parse_mode="Markdown")
            pass
    else:
        logger.warning(f"Usuario no autorizado {user_id} intentó iniciar el bot")
        await update.message.reply_text(UNAUTHORIZED_MESSAGE)
        # Si el usuario no está autorizado no se continúa
        return

    # Obtener las categorías (subdirectorios en BASE_DIR)
    categorias = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    
    # # Crear botones para cada categoría en una columna
    # keyboard = [[InlineKeyboardButton(categoria.capitalize(), callback_data=f"categoria|{categoria}")]
    #             for categoria in categorias]

    # Creo el menú con doble botonera
    keyboard = []
    row = []
    for i, categoria in enumerate(categorias, 1):
        row.append(InlineKeyboardButton(f"📂 {categoria.capitalize()}", callback_data=f"categoria|{categoria}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Verificamos nuevamente si update.message está disponible (venimos de inicio)
    if update.message:
        await update.message.reply_text("Selecciona una categoría:", reply_markup=reply_markup)
    else:
        # Si no, usamos query.message (venimos de 'volver' en el menú)
        await update.callback_query.message.reply_text("Selecciona una categoría:", reply_markup=reply_markup)


async def mostrar_recetas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra las recetas disponibles en una categoría seleccionada.

    Parameters
    ----------
    update : Update
        Objeto de actualización de Telegram.
    context : ContextTypes.DEFAULT_TYPE
        Contexto de ejecución del bot.

    Returns
    -------
    None
    """
    query = update.callback_query
    await query.answer()

    # Obtener la categoría seleccionada del callback_data
    _, categoria = query.data.split("|")
    categoria_path = os.path.join(BASE_DIR, categoria)

    # Listar los archivos PDF en la categoría seleccionada
    recetas = [f for f in os.listdir(categoria_path) if f.endswith(".pdf")]

    # Crear una estructura de teclado que simule un submenú con los botones desplazados a la derecha
    keyboard = []
    
    # Agregar una fila con un espacio vacío al principio para "desplazar" los botones
    for receta in recetas:
        # Agregar una columna vacía al principio para desplazar los botones a la derecha
        row = [InlineKeyboardButton(f" - {receta.replace('.pdf', '').capitalize()}", 
                                    callback_data=f"receta|{categoria}|{receta}")]
        keyboard.append(row)

    # Agregar un botón para volver al menú principal
    keyboard.append([InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Editar el mensaje anterior para mostrar las recetas disponibles
    await query.edit_message_text(f"📂 *Recetas en la categoría* _{categoria.capitalize()}_:", 
                                  reply_markup=reply_markup, parse_mode="Markdown")


async def enviar_receta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Envía el archivo PDF de la receta seleccionada.

    Parameters
    ----------
    update : Update
        Objeto de actualización de Telegram.
    context : ContextTypes.DEFAULT_TYPE
        Contexto de ejecución del bot.

    Returns
    -------
    None
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

    Parameters
    ----------
    update : Update
        Objeto de actualización de Telegram.
    context : ContextTypes.DEFAULT_TYPE
        Contexto de ejecución del bot.

    Returns
    -------
    None
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    logger.info(f"Usuario {user_id} ha vuelto al menú principal.")

    # Limpiar el chat: eliminar el mensaje anterior si existe
    try:
        # Eliminar el mensaje de bienvenida
        await query.message.delete()
    except Exception as e:
        logger.error(f"No se pudo eliminar el mensaje anterior: {e}")

    if user_id in AUTHORIZED_USERS:
        # Reutilizamos el 'context' para enviar el mensaje
        await start(update, context)
    else:
        logger.warning(f"Usuario no autorizado {user_id} intentó volver al menú principal.")
        await query.message.reply_text(UNAUTHORIZED_MESSAGE)


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
    Función principal para ejecutar el bot.

    Parameters
    ----------
    None

    Returns
    -------
    None
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
