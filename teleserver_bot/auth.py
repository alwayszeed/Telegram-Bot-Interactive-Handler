"""User authentication middleware for bot handlers."""

from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable

from telegram import Update


def is_authorized(user_id: int | None, allowed_user_ids: frozenset[int] | set[int]) -> bool:
    return user_id is not None and user_id in allowed_user_ids


async def deny(update: Update, reason: str = "You are not authorized to use this bot.") -> None:
    if update.callback_query is not None:
        await update.callback_query.answer(reason, show_alert=True)
        return
    if update.effective_message is not None:
        await update.effective_message.reply_text(f"⛔ {reason}")


def auth_required(
    handler: Callable[[Update, Any], Awaitable[Any]]
) -> Callable[[Update, Any], Awaitable[Any]]:
    """Wrap a handler so only allow-listed Telegram user ids can invoke it.

    Reads the Settings instance from ``context.bot_data["settings"]``.
    Works for both message handlers and callback query handlers.
    """

    @wraps(handler)
    async def wrapper(update: Update, context: Any) -> Any:
        settings = context.application.bot_data.get("settings")
        allowed = settings.allowed_user_ids if settings is not None else frozenset()
        user = update.effective_user
        if not is_authorized(user.id if user else None, allowed):
            await deny(update)
            return None
        return await handler(update, context)

    return wrapper


__all__ = ["auth_required", "deny", "is_authorized"]
