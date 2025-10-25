import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler # Додано для обробки натискань кнопок
)
from telegram.error import BadRequest

# --- Налаштування ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEBHOOK_URL = os.getenv("RENDER_URL") 

# Визначаємо режим роботи та порт
IS_WEBHOOK_MODE = bool(WEBHOOK_URL)
PORT = int(os.environ.get('PORT', 8080))

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# --------------------

# Допоміжна функція для перевірки, чи є користувач адміністратором
def is_admin(user_id):
    """Перевіряє, чи є наданий ID адміністратором."""
    try:
        return int(user_id) == int(ADMIN_ID)
    except (ValueError, TypeError):
        return False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає вітальне повідомлення та кнопки-підказки."""
    logger.info(f"Користувач {update.effective_user.id} запустив /start")

    # Створюємо кнопки-підказки
    keyboard = [
        [InlineKeyboardButton("Надіслати Заявку (Текст)", callback_data='action_text_guide')],
        [InlineKeyboardButton("Надіслати Фото", callback_data='action_photo_guide')],
        [InlineKeyboardButton("Про Бота / Допомога", callback_data='action_help_info')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привіт! ⚡ Я ваш асистент для зв'язку з адміністратором. "
        "Оберіть дію або просто надішліть своє повідомлення чи фото.",
        reply_markup=reply_markup
    )

# Обробник натискань інлайн-кнопок
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання інлайн-кнопок з вітального повідомлення."""
    query = update.callback_query
    # Відповідаємо на запит, щоб прибрати "годинник" на кнопці
    await query.answer() 

    data = query.data
    
    # Редагуємо повідомлення відповідно до натиснутої кнопки
    if data == 'action_text_guide':
        await query.edit_message_text(
            text="✍️ **Режим текстової заявки**\n\nПросто напишіть своє повідомлення або питання. Я відразу передам його адміністратору.",
            parse_mode='Markdown'
        )
    elif data == 'action_photo_guide':
        await query.edit_message_text(
            text="📸 **Режим фото**\n\nНадішліть фотографію. Ви можете додати до неї опис (підпис) для кращого розуміння.",
            parse_mode='Markdown'
        )
    elif data == 'action_help_info':
        help_text = (
            "ℹ️ **Інформація про бота**\n\n"
            "Цей бот слугує для анонімної передачі заявок та питань адміністратору. "
            "Адміністратор отримує ваше повідомлення та може відповісти вам через бота.\n\n"
            "**Важливо:** Ваш Telegram ID передається адміністратору для забезпечення можливості відповіді."
        )
        await query.edit_message_text(text=help_text, parse_mode='Markdown')


# Команда /reply для відповіді адміністратора
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Дозволяє адміністратору відповісти користувачу за його ID."""
    
    # 1. Перевірка, чи це адміністратор
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Ця команда доступна лише адміністратору.")
        return

    # 2. Перевірка аргументів: очікуємо /reply <user_id> <text>
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неправильний формат. Використовуйте: /reply <ID_користувача> <Ваша відповідь>"
        )
        return

    try:
        target_user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        
        if not reply_text:
            await update.message.reply_text("❌ Текст відповіді не може бути порожнім.")
            return

    except ValueError:
        await update.message.reply_text("❌ ID користувача має бути числовим.")
        return

    # 3. Надсилання відповіді користувачу
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"👨‍💻 **Відповідь адміністратора:**\n\n{reply_text}",
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"✅ Відповідь успішно надіслано користувачу {target_user_id}.")

    except BadRequest as e:
        logger.error(f"Помилка при надсиланні відповіді користувачу {target_user_id}: {e}")
        await update.message.reply_text(
            f"❌ Помилка: Не вдалося надіслати повідомлення користувачу {target_user_id}. Можливо, він заблокував бот або його ID невірний. ({e})"
        )
    except Exception as e:
        logger.error(f"Невідома помилка при відповіді: {e}")
        await update.message.reply_text("❌ Виникла невідома помилка при надсиланні відповіді.")


# Обробка всіх повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє вхідні повідомлення і пересилає їх адміністратору."""
    message = update.message
    user = message.from_user
    
    # Якщо це повідомлення від самого адміністратора, ігноруємо його, якщо це не /reply
    if is_admin(user.id):
        return

    # Перевірка, чи ADMIN_ID коректно встановлено
    try:
        admin_chat_id = int(ADMIN_ID)
    except (ValueError, TypeError):
        logger.error("ADMIN_ID не встановлено або має некоректний формат.")
        await message.reply_text("❌ Помилка конфігурації бота. Адміністратор не знайдений.")
        return

    # Визначаємо ім'я користувача для відображення
    user_name = user.username
    display_name = f"@{user_name}" if user_name else user.first_name
    
    # Створення шаблону повідомлення для адміна
    admin_notification = (
        f"📩 **НОВА ЗАЯВКА**\n"
        f"👤 **Користувач:** {display_name} (ID: `{user.id}`)\n"
        f"----------------------------------------\n"
        f"📝 **Зміст:** {(message.caption if message.caption else message.text if message.text else 'Фото без підпису')}\n"
        f"----------------------------------------\n"
        f"➡️ **Для відповіді:** `/reply {user.id}` <Ваша відповідь>"
    )

    is_success = False

    # Фото (тепер також перевіряємо підпис до фото - message.caption)
    if message.photo:
        photo_file = await message.photo[-1].get_file()
        try:
            await context.bot.send_photo(
                chat_id=admin_chat_id,
                photo=photo_file.file_id,
                caption=admin_notification,
                parse_mode='Markdown'
            )
            is_success = True
        except Exception as e:
            logger.error(f"Помилка при надсиланні фото адміну: {e}")

    # Текст
    elif message.text:
        try:
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=admin_notification,
                parse_mode='Markdown'
            )
            is_success = True
        except Exception as e:
            logger.error(f"Помилка при надсиланні тексту адміну: {e}")

    # Відповідь користувачу
    if is_success:
        await message.reply_text("✅ Дякую! Вашу заявку успішно передано адміністратору ⚡")
    else:
        await message.reply_text("❌ Виникла помилка при надсиланні вашої заявки адміністратору. Спробуйте пізніше.")


async def pre_run(app):
    """Функція, яка виконується перед запуском Webhook."""
    if IS_WEBHOOK_MODE and WEBHOOK_URL:
        # ПРИМУСОВЕ ВИДАЛЕННЯ СТАРОГО WEBHOOK та встановлення нового
        logger.info("Спроба видалити будь-який старий Webhook...")
        await app.bot.delete_webhook()
        logger.info("Старий Webhook видалено (якщо він був).")


def main():
    """Ініціалізує та запускає бот (Webhook для Render)."""
    if not BOT_TOKEN or not ADMIN_ID:
        logger.critical("BOT_TOKEN або ADMIN_ID не встановлено. Перевірте змінні середовища.")
        return
        
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(pre_run).build()
    
    # Додаємо хендлери
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", handle_reply)) 
    app.add_handler(CallbackQueryHandler(handle_callback_query)) # НОВИЙ ХЕНДЛЕР ДЛЯ КНОПОК
    # Обробляємо ВСІ повідомлення, крім команд
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # --- ЛОГІКА ЗАПУСКУ ---
    if IS_WEBHOOK_MODE:
        full_webhook_url = WEBHOOK_URL.rstrip('/') + '/' + BOT_TOKEN
        
        logger.info(f"✅ Режим WEBHOOK. Порт: {PORT}. URL: {full_webhook_url}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=full_webhook_url
        )

    else:
        logger.info("❌ Режим POLLING. Не знайдено RENDER_URL для Webhook.")

if __name__ == "__main__":
    main()
