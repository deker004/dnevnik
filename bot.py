import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application, ContextTypes, filters, MessageHandler

# Ваш токен от BotFather
TOKEN = "7834112722:AAHWOMS3AhirmBI5eM0g8JdniKWm75arlXE"

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

# Настройка маршрутов
starlette_app = Starlette(
    routes=[
        Route("/telegram", telegram, methods=["POST"]),  # Webhook для Telegram
        Route("/healthcheck", health, methods=["GET"]),  # Health check для Render
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
