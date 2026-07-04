"""Telegram bot — Phase 3.

Receives customer messages and forwards them to the FastAPI /chat endpoint,
using the Telegram chat_id as the session_id (per-user memory).

Dev  : long-polling  (no public URL needed)      TELEGRAM_MODE=polling
Prod : webhook       (HTTPS push from Telegram)   TELEGRAM_MODE=webhook

Run:  python -m bot.telegram_bot
"""
from src.config import settings


def main():
    if settings.telegram_mode == "webhook":
        raise NotImplementedError("Phase 3: run_webhook")
    raise NotImplementedError("Phase 3: run_polling")


if __name__ == "__main__":
    main()
