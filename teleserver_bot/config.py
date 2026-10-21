"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional
    pass


def _parse_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError as exc:
            raise ValueError(f"Invalid Telegram user id: {part!r}") from exc
    return frozenset(ids)


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    allowed_user_ids: frozenset[int]
    docker_restart_timeout: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        allowed = _parse_ids(os.getenv("TELEGRAM_ALLOWED_USER_IDS", ""))
        timeout = int(os.getenv("DOCKER_RESTART_TIMEOUT", "10"))
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")
        if not allowed:
            raise RuntimeError("TELEGRAM_ALLOWED_USER_IDS must list at least one Telegram user id.")
        return cls(bot_token=token, allowed_user_ids=allowed, docker_restart_timeout=timeout)


__all__ = ["Settings"]
