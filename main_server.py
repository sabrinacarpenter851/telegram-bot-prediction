import telegram # Змінено імпорт, щоб уникнути можливих конфліктів імен
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
import logging
import os

# --- Налаштування Render ---
# ВАЖЛИВО: Файлова система Render є ефемерною.
# Файл cards.txt буде втрачено при перезапуску/розгортанні.
# Для надійного зберігання даних на Render використовуйте:
# 1. Render Disks (https://render.com/docs/disks) - для зберігання файлів
# 2. Базу даних (наприклад, PostgreSQL від Render) - для зберігання даних
CARDS_FILENAME = "cards.txt"
# Якщо використовуєте Render Disk, шлях може бути іншим, напр. "/var/data/cards.txt"

# Логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Стан користувача (в пам'яті - теж скидається при перезапуску)
# Для стійкості стану можна розглянути telegram.ext.PicklePersistence або базу даних.
user_states = {}

# Передбачення
def generate_prediction():
    predictions = [
        "✨ Ви знайдете нові можливості в найближчому майбутньому.",
        "🔥 Час для великих змін настає.",
        "🌞 Сьогоднішній день принесе вам радість.",
        "🍀 Ваша удача незабаром буде на вашій стороні.",
        "🌱 Не бійтеся робити сміливі кроки.",
        "💪 Ваші зусилля скоро принесуть плоди.",
        "🚀 Сьогодні хороший день для нових починань.",
        "🏆 Ваша рішучість скоро призведе до успіху.",
        "🌟 Майбутнє чекає на вас з новими можливостями.",
        "⚡ Ваша енергія зараз на висоті, використовуйте її на повну.",
        "❤️ Моє улюблене ім'я Ілона",
        "🏆 Анастасії — самі класні керівниці!"
    ]
    return random.choice(predictions)

# Функція для створення головного меню
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🔮 Моє передбачення")],
        [KeyboardButton("📜 Моя пропозиція")], # Уніфіковано текст кнопки
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = "main_menu" # Встановлюємо стан
    logger.info(f"User {user_id} started the bot.")
    await update.message.reply_text(
        "Привіт! 👋 Обери одну з опцій:",
        reply_markup=get_main_menu_keyboard()
    )

# Функція "Моє передбачення"
async def get_prediction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # Перевірка, чи користувач у головному меню (за бажанням, для строгості)
    # if user_states.get(user_id) != "main_menu":
    #     await update.message.reply_text("Будь ласка, спочатку поверніться в головне меню.", reply_markup=get_main_menu_keyboard())
    #     return

    prediction = generate_prediction()
    keyboard = [[KeyboardButton("🔙 Назад")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) # one_time_keyboard=True може бути зручніше для "Назад"
    await update.message.reply_text(f"Ваше передбачення:\n\n{prediction}", reply_markup=reply_markup)
    # Не змінюємо стан тут, бо користувач може захотіти ще передбачення або повернутись

# Функція "Моя пропозиція" (запит картки)
async def request_card_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = "awaiting_card" # Встановлюємо стан очікування картки
    logger.info(f"User {user_id} requested offer, awaiting card.")
    # Не показуємо клавіатуру тут, чекаємо на текстове введення номера картки
    await update.message.reply_text(
        "Будь ласка, введіть номер вашої картки лояльності (14 цифр, починається з '02'):",
        # Можна прибрати клавіатуру взагалі на цьому кроці
        reply_markup=telegram.ReplyKeyboardRemove()
        # Або залишити тільки кнопку Назад
        # reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True, one_time_keyboard=True)
    )

# Обробка текстових повідомлень
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    current_state = user_states.get(user_id, "main_menu") # Отримуємо стан або вважаємо, що це головне меню

    logger.info(f"User {user_id} (state: {current_state}) sent text: {text}")

    # --- Обробка кнопки "Назад" ---
    if text == "🔙 Назад":
        user_states[user_id] = "main_menu" # Повертаємо в головне меню
        await update.message.reply_text(
            "Повертаємося до головного меню. Обери одну з опцій:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    # --- Обробка залежно від стану ---
    if current_state == "awaiting_card":
        # Перевірка формату картки
        if text.startswith("02") and len(text) == 14 and text.isdigit():
            logger.info(f"User {user_id} submitted potentially valid card: {text}")
            # Запис у файл (з перевіркою на дублікати)
            try:
                # Перевірка існування та створення файлу/директорій, якщо потрібно
                file_dir = os.path.dirname(CARDS_FILENAME)
                if file_dir and not os.path.exists(file_dir):
                     os.makedirs(file_dir)
                     logger.info(f"Created directory: {file_dir}")
                if not os.path.exists(CARDS_FILENAME):
                    with open(CARDS_FILENAME, "w", encoding="utf-8") as f:
                        f.write("") # Створюємо порожній файл
                    logger.info(f"Created file: {CARDS_FILENAME}")


                # Читання існуючих карток
                with open(CARDS_FILENAME, "r", encoding="utf-8") as f:
                    cards = {line.strip() for line in f if line.strip()} # Використовуємо set для ефективності

                # Запис, якщо картка унікальна
                if text not in cards:
                    with open(CARDS_FILENAME, "a", encoding="utf-8") as f:
                        f.write(f"{text}\n")
                    logger.info(f"User {user_id} card {text} saved to {CARDS_FILENAME}")
                else:
                    logger.info(f"User {user_id} card {text} already exists in {CARDS_FILENAME}")

                # Повернення в головне меню і відправка пропозиції
                user_states[user_id] = "main_menu"
                await update.message.reply_text(
                    "✅ Дякуємо! Вашу картку прийнято.\n\nОсь ваша ексклюзивна пропозиція:\nhttps://instagram.com/romankuryn",
                    reply_markup=get_main_menu_keyboard() # Відразу показуємо головне меню
                )

            except Exception as e:
                logger.error(f"Error handling card file for user {user_id}: {e}", exc_info=True)
                await update.message.reply_text(
                    "Виникла помилка при збереженні картки. Спробуйте пізніше або зверніться до підтримки.",
                    reply_markup=get_main_menu_keyboard()
                )
                user_states[user_id] = "main_menu" # Повертаємо в меню при помилці

        else:
            logger.warning(f"User {user_id} submitted invalid card format: {text}")
            await update.message.reply_text(
                "❌ Невірний формат номеру картки.\nБудь ласка, введіть рівно 14 цифр, що починаються з '02'. Спробуйте ще раз або натисніть '🔙 Назад'.",
                 # Залишаємо користувача в стані awaiting_card
                 # Можна додати кнопку "Назад" сюди, якщо прибрали її раніше
                 reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True, one_time_keyboard=True)
            )

    elif current_state == "main_menu":
        if text == "🔮 Моє передбачення":
            await get_prediction_handler(update, context)
        elif text == "📜 Моя пропозиція": # Уніфіковано текст кнопки
            await request_card_handler(update, context)
        else:
            # Якщо отримано невідомий текст у головному меню
            await update.message.reply_text(
                "Не зрозумів команду 🤔. Будь ласка, скористайся кнопками нижче або введи /start.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        # Обробка невідомого стану (не повинно траплятися, але про всяк випадок)
        logger.warning(f"User {user_id} is in unknown state: {current_state}. Resetting to main_menu.")
        user_states[user_id] = "main_menu"
        await update.message.reply_text(
            "Щось пішло не так. Повертаю вас у головне меню.",
            reply_markup=get_main_menu_keyboard()
        )


# Функція обробки помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Loggує помилки, спричинені Updates."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    # За бажанням, можна спробувати повідомити користувача про помилку
    # if isinstance(update, Update) and update.effective_message:
    #     try:
    #         await update.effective_message.reply_text("Ой, сталася внутрішня помилка. Ми вже працюємо над цим!")
    #     except Exception as e:
    #         logger.error(f"Failed to send error message to user: {e}")


# Основна функція
def main() -> None:
    # Перевірка наявності токена
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.critical("Помилка: Змінна середовища BOT_TOKEN не встановлена!")
        return

    # Створення Application
    application = Application.builder().token(bot_token).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    # Використовуємо фільтри для розділення обробки кнопок/тексту
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Реєструємо обробник помилок
    application.add_error_handler(error_handler)

    # Запускаємо бота
    logger.info("Starting bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES) # Явно вказуємо типи оновлень

if __name__ == '__main__':
    main()