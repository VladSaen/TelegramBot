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

# --- Налаштування ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_URL = os.getenv("RENDER_URL") # Використовуємо змінну, яку ви вже встановили

# Визначаємо режим роботи. Якщо WEBHOOK_URL є, ми в режимі Webhook.
IS_WEBHOOK_MODE = bool(WEBHOOK_URL)

# Порт, який надає Render
PORT = int(os.environ.get('PORT', 8080))

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# --------------------

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
        logger.error("ADMIN_ID не встановлено або має некоректний формат.")
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


async def pre_run(app):
    """Функція, яка виконується перед запуском Webhook."""
    if IS_WEBHOOK_MODE and WEBHOOK_URL:
        # ПРИМУСОВЕ ВИДАЛЕННЯ СТАРОГО WEBHOOK
        logger.info("Спроба видалити будь-який старий Webhook...")
        await app.bot.delete_webhook()
        logger.info("Старий Webhook видалено (якщо він був).")


def main():
    """Ініціалізує та запускає бот (Webhook для Render, Polling в іншому випадку)."""
    if not BOT_TOKEN or not ADMIN_ID:
        logger.critical("BOT_TOKEN або ADMIN_ID не встановлено. Перевірте змінні середовища.")
        return
        
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(pre_run).build()
    
    # Додаємо хендлери
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # --- ЛОГІКА ЗАПУСКУ ---
    if IS_WEBHOOK_MODE:
        # Режим Webhook для продакшен-середовища (Render)
        full_webhook_url = WEBHOOK_URL.rstrip('/') + '/' + BOT_TOKEN
        
        logger.info(f"✅ Режим WEBHOOK. Порт: {PORT}. URL: {full_webhook_url}")
        
        # Це дозволяє Application працювати як ASGI-застосунок, який може приймати запити від Render.
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=full_webhook_url
        )

    else:
        # Режим Polling для локальної розробки (це те, що у вас зараз відбувається на Render)
        logger.info("❌ Режим POLLING. Не знайдено RENDER_URL для Webhook.")
        # Щоб уникнути Conflict error, ми не будемо запускати Polling на Render
        # Якщо Render_URL не встановлено, логіка Webhook не спрацьовує, і бот просто завершить роботу
        # Це запобігає зависанню служби Render.
        
        # app.run_polling(poll_interval=10) # Закоментуємо, щоб не конфліктувати
        logger.info("Бот не запущено в режимі Polling для уникнення помилок Render.")

if __name__ == "__main__":
    main()
