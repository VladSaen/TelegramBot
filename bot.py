from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔹 Вставлені дані
BOT_TOKEN = "8360851970:AAGccVI4BkWHJJHMvTgHMS4a--Rz2NBQlVA"
ADMIN_ID = 5828362947  # твій Telegram ID

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю! 🛠️ Напишіть, що сталося — і я передам це електрику.\n"
        "Можна надіслати текст або фото."
    )

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_name = message.from_user.username or message.from_user.first_name

    if message.photo:
        # Фото у максимальній якості
        photo_file = await message.photo[-1].get_file()
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file.file_id,
                                     caption=f"📷 Фото від {user_name}")
    elif message.text:
        await context.bot.send_message(chat_id=ADMIN_ID,
                                       text=f"📩 Заявка від {user_name}:\n{message.text}")

    await message.reply_text("✅ Дякую! Заявку передано ⚡")

# Створюємо і запускаємо бот
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

app.run_polling()
