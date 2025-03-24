import sys
import os
# Agregar el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest
from settings import *
from log.logger import logger
import asyncio


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

    # Añado el reset también en el menú principal

    # Agregar un botón para buscar recetas y el botón de reiniciar
    keyboard.append([InlineKeyboardButton("🔍 Buscar recetas", callback_data="buscar_recetas")])
    keyboard.append([InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Verificamos nuevamente si update.message está disponible (venimos de inicio)
    if update.message:
        await update.message.reply_text("Selecciona una categoría o busca una receta:", reply_markup=reply_markup)
    else:
        # Si no, usamos query.message (venimos de 'volver' en el menú)
        await update.callback_query.message.reply_text("Selecciona una categoría o busca una receta (usa palabras representativas)", reply_markup=reply_markup)
        keyboard.append([InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")])

    # reply_markup = InlineKeyboardMarkup(keyboard)
    
    # # Verificamos nuevamente si update.message está disponible (venimos de inicio)
    # if update.message:
    #     await update.message.reply_text("Selecciona una categoría:", reply_markup=reply_markup)
    # else:
    #     # Si no, usamos query.message (venimos de 'volver' en el menú)
    #     await update.callback_query.message.reply_text("Selecciona una categoría:", reply_markup=reply_markup)


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
    keyboard.append([InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Editar el mensaje anterior para mostrar las recetas disponibles
    await query.edit_message_text(f"📂 *Recetas en la categoría* _{categoria.capitalize()}_:", 
                                  reply_markup=reply_markup, parse_mode="Markdown")


async def enviar_receta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Envía el archivo PDF de la receta seleccionada. Muestra una barra de progreso
    animada para que el usuario entienda que se está descargando.

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

    # Mensaje inicial con barra vacía
    progress_template = "Preparando receta: [{bar}] {percent}%"
    progress_bar = "░░░░░░░░░░"  # 10 bloques vacíos
    message = await query.edit_message_text(progress_template.format(bar=progress_bar, percent=0))

    # Para la simulación de la barra de progreso con actualizaciones
    progress_steps = ["█░░░░░░░░░", "██░░░░░░░░", "███░░░░░░░", "████░░░░░░",
                      "█████░░░░░", "██████░░░░", "███████░░░", "████████░░",
                      "█████████░", "██████████"]
    # Simulación de la barra de progreso
    for i, step in enumerate(progress_steps):
        await asyncio.sleep(0.5)  # Pequeño retraso para la animación
        await message.edit_text(progress_template.format(bar=step, percent=(i + 1) * 10))

    # Crear botón para volver al menú principal
    # keyboard = [[InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")]]
    keyboard = [
        [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")],
        [InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar el archivo PDF después de completar la "descarga"
    try:
        await context.bot.send_document(chat_id=query.message.chat_id, document=open(receta_path, "rb"))
        await query.message.reply_text("Ya puedes descargar la receta 😊", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error al enviar la receta {receta_pdf}: {e}")
        await query.message.reply_text("❌ Hubo un error al enviar la receta. Inténtalo nuevamente más tarde.", reply_markup=reply_markup)


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


async def search_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Busca recetas basadas en el nombre de la receta.
    
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
    query = update.message.text.lower()

    if user_id not in AUTHORIZED_USERS:
        logger.warning(f"Usuario no autorizado {user_id} intentó buscar recetas.")
        await update.message.reply_text(UNAUTHORIZED_MESSAGE)
        return

    logger.info(f"Usuario {user_id} busca recetas con: {query}")

    # Obtener todas las categorías (subdirectorios en BASE_DIR)
    categorias = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]

    # Buscar recetas que coincidan con la consulta en cada categoría
    resultados = []
    for categoria in categorias:
        categoria_path = os.path.join(BASE_DIR, categoria)
        for receta in os.listdir(categoria_path):
            if receta.endswith(".pdf") and query in receta.lower():
                resultados.append((categoria, receta))

    # Verificar si se encontraron resultados
    if resultados:
        # Crear botones con los resultados encontrados
        keyboard = [
            [InlineKeyboardButton(f" - {receta.replace('.pdf', '').capitalize()}", 
                                 callback_data=f"receta|{categoria}|{receta}")]
            for categoria, receta in resultados
        ]
        
        keyboard.append([InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")])
        keyboard.append([InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"📝 Resultados para '{query}':", reply_markup=reply_markup)

    else:
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="volver")],
            [InlineKeyboardButton("❌ Reiniciar el bot", callback_data="reset")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"No se encontraron recetas que coincidan con '{query}'. Puedes seguir buscando o usar los botones:", reply_markup=reply_markup)


async def iniciar_busqueda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Inicia la búsqueda de recetas cuando el usuario presiona el botón de 'Buscar recetas'.
    
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
    logger.info(f"Usuario {user_id} ha iniciado la búsqueda de recetas.")

    # Limpiar el chat: eliminar el mensaje anterior si existe
    try:
        # Eliminar el mensaje de bienvenida
        await query.message.delete()
    except Exception as e:
        logger.error(f"No se pudo eliminar el mensaje anterior: {e}")

    if user_id in AUTHORIZED_USERS:
        await query.message.reply_text("Indica alguna palabra representativa de la receta que buscas", parse_mode="Markdown")
    else:
        logger.warning(f"Usuario no autorizado {user_id} intentó buscar recetas.")
        await query.message.reply_text(UNAUTHORIZED_MESSAGE)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Restablece la sesión del usuario y elimina todos los mensajes del chat.

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
    chat_id = query.message.chat_id
    logger.info(f"Usuario {user_id} ha solicitado un reseteo completo del chat.")

    # Limpiar los datos almacenados del usuario
    context.user_data.clear()

    # Intentar eliminar los últimos mensajes del bot en paralelo
    try:
        message_id = query.message.message_id
        delete_tasks = []

        # Intentamos eliminar los últimos 200 mensajes del bot (ajustable según necesidad)
        for msg_id in range(message_id, message_id - 200, -1):
            delete_tasks.append(context.bot.delete_message(chat_id=chat_id, message_id=msg_id))

        # Ejecutamos todas las eliminaciones en paralelo
        await asyncio.gather(*delete_tasks)

    except BadRequest as e:
        logger.warning(f"Finalizada limpieza")

    except Exception as e:
        logger.error(f"Error al intentar limpiar el chat: {e}")


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

    # Manejador para capturar cualquier mensaje de texto y buscar recetas
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_recipe))

    # CallbackQueryHandlers para manejar interacciones con botones
    app.add_handler(CallbackQueryHandler(mostrar_recetas, pattern="^categoria\\|"))
    app.add_handler(CallbackQueryHandler(enviar_receta, pattern="^receta\\|"))
    app.add_handler(CallbackQueryHandler(volver_menu_principal, pattern="^volver$"))
    app.add_handler(CallbackQueryHandler(reset, pattern="^reset$"))
    app.add_handler(CallbackQueryHandler(iniciar_busqueda, pattern="^buscar_recetas$"))

    
    # Iniciar el bot en modo polling (consulta continua)
    logger.info("Bot iniciado y ejecutándose...")
    app.run_polling()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
