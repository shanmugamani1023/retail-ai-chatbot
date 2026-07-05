"""Telegram bot — Phase 3.

A thin layer: it receives customer messages and forwards them to the FastAPI
/chat endpoint, using the Telegram chat_id as the session_id (so each user gets
their own memory). It then sends the agent's reply back.

Dev  : long-polling  (no public URL needed)      TELEGRAM_MODE=polling
Prod : webhook       (HTTPS push from Telegram)   TELEGRAM_MODE=webhook

Run (dev):  python -m bot.telegram_bot
Requires the API to be running:  uvicorn api.main:app
"""
import logging

import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.config import settings

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
log = logging.getLogger("telegram_bot")

WELCOME = (
    "👋 Hi! I'm your shopping assistant.\n\n"
    "Ask me about our products — for example:\n"
    "• How many HP shampoos are in stock?\n"
    "• Recommend something for dandruff\n"
    "• What's the cheapest soda?\n\n"
    "How can I help you today?"
)

TG_MAX = 4096  # Telegram message length limit


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = update.message.text
    log.info("msg from %s: %s", chat_id, text)

    # show "typing..." while the agent works
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.api_url}/chat",
                json={"message": text, "session_id": str(chat_id)},
            )
            resp.raise_for_status()
            answer = resp.json().get("answer", "Sorry, something went wrong.")
    except Exception as exc:  # network / API down / timeout
        log.error("API call failed: %s", exc)
        answer = "Sorry, I'm having trouble right now. Please try again in a moment."

    # split long replies across messages (Telegram caps at 4096 chars)
    for i in range(0, len(answer), TG_MAX):
        await update.message.reply_text(answer[i : i + TG_MAX])


def build_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


def main() -> None:
    app = build_app()
    if settings.telegram_mode == "webhook":
        log.info("Starting in WEBHOOK mode at %s", settings.webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=8080,
            webhook_url=settings.webhook_url,
        )
    else:
        log.info("Starting in POLLING mode. Press Ctrl+C to stop.")
        app.run_polling()


if __name__ == "__main__":
    main()
