import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# Налаштування логування для кращої діагностики
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота і твій Telegram ID
# Використовуємо змінні середовища. Hardcode видалено!
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає вітальне повідомлення."""
    logger.info(f"Користувач {update.effective_user.id} запустив /start")
    await update.message.reply_text(
        "Привіт! ⚡ Надішліть заявку або фото, і я передам це адміністратору."
    )

# Обробка всіх повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє вхідні повідомлення (текст або фото) і пересилає їх адміністратору."""
    message = update.message
    user_name = message.from_user.username or message.from_user.first_name
    
    # Перевірка, чи ADMIN_ID коректно встановлено
    try:
        admin_chat_id = int(ADMIN_ID)
    except (ValueError, TypeError):
        logger.error("ADMIN_ID не встановлено або має некоректний формат (потрібне ціле число).")
        await message.reply_text("❌ Помилка конфігурації бота. Адміністратор не знайдений.")
        return

    # Фото
    if message.photo:
        photo_file = await message.photo[-1].get_file()
        try:
            await context.bot.send_photo(
                chat_id=admin_chat_id,
                photo=photo_file.file_id,
                caption=f"📷 Фото від @{user_name} ({message.from_user.id})"
            )
        except Exception as e:
            logger.error(f"Помилка при надсиланні фото адміну: {e}")
            await message.reply_text("❌ Виникла помилка при надсиланні фото адміністратору.")
            return

    # Текст
    elif message.text:
        try:
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"📩 Заявка від @{user_name} ({message.from_user.id}):\n{message.text}"
            )
        except Exception as e:
            logger.error(f"Помилка при надсиланні тексту адміну: {e}")
            await message.reply_text("❌ Виникла помилка при надсиланні заявки адміністратору.")
            return

    # Відповідь користувачу
    await message.reply_text("✅ Дякую! Заявку передано ⚡")

def main():
    """Запускає бот."""
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN не встановлено. Бот не може запуститися.")
        print("ПОМИЛКА: Змінна середовища BOT_TOKEN має бути встановлена.")
        return

    if not ADMIN_ID:
        logger.critical("ADMIN_ID не встановлено. Бот не може запуститися.")
        print("ПОМИЛКА: Змінна середовища ADMIN_ID має бути встановлена.")
        return
        
    logger.info("Ініціалізація бота...")
    
    try:
        # Створюємо додаток
        # ApplicationBuilder().token(BOT_TOKEN).build() - це правильний спосіб у ptb v20+
        app = ApplicationBuilder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.critical(f"Помилка при ініціалізації ApplicationBuilder: {e}")
        return

    # Додаємо хендлери
    app.add_handler(CommandHandler("start", start))
    # filters.ALL & ~filters.COMMAND - це правильно для обробки всіх повідомлень, крім команд
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    logger.info("Бот запущено (Polling mode)...")
    # Запускаємо бот
    app.run_polling()

if __name__ == "__main__":
    main()
