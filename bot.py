# bot.py
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Токен бота і твій Telegram ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "8360851970:AAGccVI4BkWHJJHMvTgHMS4a--Rz2NBQlVA")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5828362947"))

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! ⚡ Надішліть заявку або фото, і я передам це адміністратору."
    )

# Обробка всіх повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_name = message.from_user.username or message.from_user.first_name

    # Фото
    if message.photo:
        photo_file = await message.photo[-1].get_file()
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file.file_id,
            caption=f"📷 Фото від {user_name}"
        )
    # Текст
    elif message.text:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Заявка від {user_name}:\n{message.text}"
        )

    await message.reply_text("✅ Дякую! Заявку передано ⚡")

def main():
    # Створюємо додаток і додаємо хендлери
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # Запускаємо бот
    app.run_polling()

if __name__ == "__main__":
    main()
