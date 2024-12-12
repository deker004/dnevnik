import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application, ContextTypes, filters, MessageHandler

TOKEN = os.getenv("7834112722:AAHWOMS3AhirmBI5eM0g8JdniKWm75arlXE")
URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = 8000

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

async def telegram(request: Request) -> Response:
    application = Application.builder().token(TOKEN).updater(None).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    await application.update_queue.put(Update.de_json(data=await request.json(), bot=application.bot))
    return Response()

async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse(content="The bot is still running fine :)")

starlette_app = Starlette(
    routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/healthcheck", health, methods=["GET"]),
    ]
)

async def main():
    config = uvicorn.Config(app=starlette_app, port=PORT, host="0.0.0.0")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
