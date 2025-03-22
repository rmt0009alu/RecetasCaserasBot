import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

# Lista de usuarios autorizados (puedes almacenarla en un archivo o base de datos)
AUTHORIZED_USERS = [123456789, 987654321]  # Reemplaza con los IDs de usuario reales

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in AUTHORIZED_USERS:
        await update.message.reply_text('Bienvenido al buscador de recetas. ¿Qué receta buscas?')
    else:
        await update.message.reply_text('Lo siento, no tienes autorización para usar este bot.')

async def search_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_USERS:
        query = update.message.text.lower()
        # Aquí implementarías la lógica de búsqueda en tus archivos PDF o TEX
        # Por ahora, solo responderemos con un mensaje genérico
        await update.message.reply_text(f"Buscando recetas que contengan: {query}")
    else:
        await update.message.reply_text('Lo siento, no tienes autorización para usar este bot.')

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_recipe))
    
    app.run_polling()
