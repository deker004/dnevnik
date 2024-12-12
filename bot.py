import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application, ContextTypes, filters, MessageHandler

# Токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден. Убедитесь, что переменная окружения задана.")

# Функция для обработки сообщений
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на текстовые сообщения."""
    await update.message.reply_text(f"Вы сказали: {update.message.text}")

# Обработчик для Telegram webhook
async def telegram(request: Request) -> Response:
    """Обрабатывает входящие запросы от Telegram."""
    application = Application.builder().token(TOKEN).updater(None).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    await application.update_queue.put(Update.de_json(data=await request.json(), bot=application.bot))
    return Response()

# Health check для Render
async def health(_: Request) -> PlainTextResponse:
    """Проверка работоспособности сервиса."""
    return PlainTextResponse(content="The bot is still running fine :)")

# Обработчик для корневого маршрута /
async def home(_: Request) -> PlainTextResponse:
    """Обрабатывает запросы на корневой маршрут."""
    return PlainTextResponse(content="Welcome to the Telegram bot service!")

# Обработчик для POST-запросов на корневой маршрут /
async def handle_post(_: Request) -> PlainTextResponse:
    """Обрабатывает POST-запросы на корневой маршрут."""
    return PlainTextResponse(content="POST requests are not allowed here.", status_code=405)

# Настройка маршрутов
starlette_app = Starlette(
    routes=[
        Route("/telegram", telegram, methods=["POST"]),  # Webhook для Telegram
        Route("/healthcheck", health, methods=["GET"]),  # Health check для Render
        Route("/", home, methods=["GET"]),  # Корневой маршрут
        Route("/", handle_post, methods=["POST"]),  # Обработка POST-запросов на /
    ]
)

# Основная функция для запуска сервера
async def main():
    """Запускает сервер."""
    config = uvicorn.Config(app=starlette_app, port=8000, host="0.0.0.0")
    server = uvicorn.Server(config)
    await server.serve()

# Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
# Хранилище записей (в памяти)
user_data = {}

# Функция для создания инлайн-клавиатуры
def create_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Добавить запись", callback_data="add")],
        [InlineKeyboardButton("Показать записи", callback_data="show")],
        [InlineKeyboardButton("Редактировать запись", callback_data="edit")],
        [InlineKeyboardButton("Удалить запись", callback_data="delete")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и меню бота."""
    await update.message.reply_text(
        "Привет! Я твой дневник успеха. Выбери действие:",
        reply_markup=create_menu_keyboard()
    )

# Обработка инлайн-кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на инлайн-кнопки."""
    query = update.callback_query
    await query.answer()

    if query.data == "add":
        await query.edit_message_text("Напиши свою запись в формате:\n"
                                      "Достижения: <текст>\n"
                                      "Уроки: <текст>\n"
                                      "Планы: <текст>")
        context.user_data["state"] = "add"
    elif query.data == "show":
        await show_entries(update, context)
    elif query.data == "edit":
        await query.edit_message_text("Отправь номер записи, которую хочешь отредактировать.")
        context.user_data["state"] = "edit_select"
    elif query.data == "delete":
        await query.edit_message_text("Отправь номер записи, которую хочешь удалить.")
        context.user_data["state"] = "delete_select"

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения от пользователя."""
    user_id = update.message.from_user.id
    text = update.message.text

    if "state" in context.user_data:
        if context.user_data["state"] == "add":
            # Добавление новой записи
            entry = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "text": text
            }
            if user_id not in user_data:
                user_data[user_id] = []
            user_data[user_id].append(entry)
            await update.message.reply_text("Запись добавлена!", reply_markup=create_menu_keyboard())
            del context.user_data["state"]
        elif context.user_data["state"] == "edit_select":
            # Выбор записи для редактирования
            try:
                entry_id = int(text) - 1
                if 0 <= entry_id < len(user_data[user_id]):
                    context.user_data["edit_entry_id"] = entry_id
                    await update.message.reply_text("Отправь новый текст для записи.")
                    context.user_data["state"] = "edit_confirm"
                else:
                    await update.message.reply_text("Неверный номер записи. Попробуй еще раз.")
            except ValueError:
                await update.message.reply_text("Пожалуйста, отправь номер записи.")
        elif context.user_data["state"] == "edit_confirm":
            # Подтверждение редактирования
            entry_id = context.user_data["edit_entry_id"]
            user_data[user_id][entry_id]["text"] = text
            await update.message.reply_text("Запись обновлена!", reply_markup=create_menu_keyboard())
            del context.user_data["state"]
            del context.user_data["edit_entry_id"]
        elif context.user_data["state"] == "delete_select":
            # Удаление записи
            try:
                entry_id = int(text) - 1
                if 0 <= entry_id < len(user_data[user_id]):
                    user_data[user_id].pop(entry_id)
                    await update.message.reply_text("Запись удалена!", reply_markup=create_menu_keyboard())
                else:
                    await update.message.reply_text("Неверный номер записи. Попробуй еще раз.")
            except ValueError:
                await update.message.reply_text("Пожалуйста, отправь номер записи.")
            del context.user_data["state"]
    else:
        await update.message.reply_text("Используй меню для взаимодействия с ботом.", reply_markup=create_menu_keyboard())

# Показать записи
async def show_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает все записи пользователя."""
    user_id = update.callback_query.from_user.id
    if user_id in user_data and user_data[user_id]:
        entries = "\n".join(
            [f"{i + 1}. {entry['time']}: {entry['text']}" for i, entry in enumerate(user_data[user_id])]
        )
        await update.callback_query.edit_message_text(f"Ваши записи:\n{entries}", reply_markup=create_menu_keyboard())
    else:
        await update.callback_query.edit_message_text("У вас пока нет записей.", reply_markup=create_menu_keyboard())

# Основная функция для запуска бота
def main():
    """Запускает бота."""
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
