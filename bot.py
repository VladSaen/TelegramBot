import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8360851970:AAGccVI4BkWHJJHMvTgHMS4a--Rz2NBQlVA"
ADMIN_ID = 5828362947  # Твій Telegram ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я бот електрика. Напиши, що в тебе сталося — і я передам повідомлення.")

# коли користувач пише повідомлення
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text or ""
    caption = update.message.caption or ""

    # якщо користувач надсилає фото з підписом
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=f"📩 Заявка від @{user.username or user.first_name}:\n{caption}"
        )
        await update.message.reply_text("Дякую! Фото й опис відправлено ⚡️")
    else:
        msg = f"📩 Заявка від @{user.username or user.first_name}:\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("Дякую! Твою заявку передано ⚡️")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
