"""Inline keyboard layouts for the bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

STATUS = "menu:status"
CONTAINERS = "menu:containers"
REFRESH = "menu:refresh"
HELP = "menu:help"


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Status", callback_data=STATUS),
                InlineKeyboardButton("🐳 Containers", callback_data=CONTAINERS),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=REFRESH),
                InlineKeyboardButton("ℹ️ Help", callback_data=HELP),
            ],
        ]
    )


def containers_menu(containers: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if not containers:
        rows.append([InlineKeyboardButton("No containers found", callback_data="noop")])
    for container in containers[:20]:
        state = "🟢" if container["state"] == "running" else "🔴"
        rows.append(
            [
                InlineKeyboardButton(
                    f"{state} {container['name']} ({container['state']})",
                    callback_data=f"container:info:{container['name']}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton("🔄 Refresh containers", callback_data=CONTAINERS),
            InlineKeyboardButton("⬅️ Back", callback_data="menu:home"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def container_actions(container: dict) -> InlineKeyboardMarkup:
    name = container["name"]
    rows = [
        [InlineKeyboardButton("🔁 Restart", callback_data=f"container:restart:{name}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=CONTAINERS)],
    ]
    return InlineKeyboardMarkup(rows)


def restart_confirmation(name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes, restart", callback_data=f"container:confirm:{name}"),
                InlineKeyboardButton("✖️ Cancel", callback_data=f"container:info:{name}"),
            ]
        ]
    )


__all__ = [
    "CONTAINERS",
    "HELP",
    "REFRESH",
    "STATUS",
    "container_actions",
    "containers_menu",
    "main_menu",
    "restart_confirmation",
]
