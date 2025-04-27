import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random

# Логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Стан користувача
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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_states[user_id] = "main_menu"

    keyboard = [
        [KeyboardButton("🔮 Моє передбачення")],
        [KeyboardButton("💡 Моя пропозиція")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привіт! Обери одну з опцій:", reply_markup=reply_markup)

# Функція "Моє передбачення"
async def get_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prediction = generate_prediction()
    keyboard = [[KeyboardButton("🔙 Назад")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Ваше передбачення: {prediction}", reply_markup=reply_markup)

# Обробка тексту
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Обробка кнопки "Назад"
    if text == "🔙 Назад":
        user_states[user_id] = "main_menu"
        keyboard = [
            [KeyboardButton("🔮 Моє передбачення")],
            [KeyboardButton("📜 Моя пропозиція")],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Повертаємося до головного меню. Обери одну з опцій:", reply_markup=reply_markup)
        return

    # Якщо очікується введення картки
    if user_states.get(user_id) == "awaiting_card":
        if text.startswith("02") and len(text) == 14 and text.isdigit():
            # Запис у файл (перевірка на дублікати)
            filename = "cards.txt"
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("")

            with open(filename, "r", encoding="utf-8") as f:
                cards = f.read().splitlines()

            if text not in cards:
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(f"{text}\n")

            user_states[user_id] = "main_menu"
            keyboard = [[KeyboardButton("🔙 Назад")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Дякуємо!\nОсь твоя пропозиція: https://instagram.com/romankuryn", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Невірний номер картки. Має бути 14 цифр.")
    else:
        # Інші команди
        if text == "🔮 Моє передбачення":
            await get_prediction(update, context)
        elif text == "📜 Моя пропозиція":
            user_states[user_id] = "awaiting_card"
            await update.message.reply_text("Введи номер картки лояльності (14 цифр):")
        else:
            await update.message.reply_text("Не зрозумів команду. Натисни /start або скористайся кнопками.")

# Основна функція
def main() -> None:
    # Отримання токену з змінної середовища
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не знайдений у змінних середовища!")

    # Створення об'єкта додатка з токеном
    application = Application.builder().token(bot_token).build()

    # Додаємо хендлери
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Запускаємо бота
    application.run_polling()

if __name__ == '__main__':
    main()
