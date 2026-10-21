"""Entry point for the Teleserver Pulse Telegram bot."""

from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from .auth import auth_required
from .config import Settings
from .handlers import (
    button_handler,
    containers_command,
    error_handler,
    help_command,
    start,
    status_command,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("teleserver-pulse-bot")


def build_application(settings: Settings | None = None) -> Application:
    settings = settings or Settings.from_env()
    application = ApplicationBuilder().token(settings.bot_token).build()
    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("containers", containers_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    settings = Settings.from_env()
    application = build_application(settings)
    logger.info("Teleserver Pulse bot starting with %d authorized user(s)", len(settings.allowed_user_ids))
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":  # pragma: no cover
    main()
