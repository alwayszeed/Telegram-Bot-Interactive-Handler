"""Telegram handlers: status, container list, restart flow."""

from __future__ import annotations

import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .auth import auth_required
from .keyboards import (
    CONTAINERS,
    HELP,
    REFRESH,
    STATUS,
    container_actions,
    containers_menu,
    main_menu,
    restart_confirmation,
)
from .metrics import human_bytes, list_containers, restart_container, system_summary

WELCOME = (
    "🩺 *Teleserver Pulse*\n\n"
    "Monitor server dan kontrol kontainer Docker langsung dari Telegram.\n"
    "Gunakan tombol di bawah untuk mulai."
)


def _format_status() -> str:
    data = system_summary()
    lines = [
        "📊 *System Status*",
        f"Host: `{data['hostname']}` ({data['platform']})",
        f"CPU: *{data['cpu_percent']}%* across {data['cpu_count']} cores",
        f"RAM: *{data['memory_percent']}%* "
        f"({human_bytes(data['memory_used'])} / {human_bytes(data['memory_total'])})",
        f"Disk: *{data['disk_percent']}%* "
        f"({human_bytes(data['disk_used'])} / {human_bytes(data['disk_total'])})",
        f"Uptime: {data['uptime_seconds'] / 3600:.1f} jam",
        f"Updated: `{data['timestamp']}`",
    ]
    if data.get("load_average"):
        load = ", ".join(f"{value:.2f}" for value in data["load_average"])
        lines.insert(3, f"Load avg: {load}")
    return "\n".join(lines)


async def _safe_containers() -> tuple[list[dict], str | None]:
    try:
        return await asyncio.to_thread(list_containers), None
    except RuntimeError as exc:
        return [], str(exc)


@auth_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            WELCOME, parse_mode="Markdown", reply_markup=main_menu()
        )


@auth_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            "ℹ️ *Commands*\n"
            "/start — menu utama\n"
            "/status — status CPU/RAM/disk real-time\n"
            "/containers — daftar kontainer Docker\n"
            "/help — bantuan\n\n"
            "Tombol inline: *Status*, *Containers*, *Refresh*, *Restart*.",
            parse_mode="Markdown",
            reply_markup=main_menu(),
        )


@auth_required
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text(
            _format_status(), parse_mode="Markdown", reply_markup=main_menu()
        )


@auth_required
async def containers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    containers, error = await _safe_containers()
    if update.effective_message:
        if error:
            await update.effective_message.reply_text(f"⚠️ {error}", reply_markup=main_menu())
            return
        await update.effective_message.reply_text(
            f"🐳 *Containers* ({len(containers)})\nPilih kontainer untuk detail atau restart.",
            parse_mode="Markdown",
            reply_markup=containers_menu(containers),
        )


@auth_required
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    data = query.data or ""

    if data == "noop":
        await query.answer("Nothing to do.")
        return

    if data in ("menu:home", HELP):
        await query.answer()
        text = WELCOME if data != HELP else "Pilih menu di bawah untuk melihat status atau kontainer."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())
        return

    if data in (STATUS, REFRESH):
        await query.answer("Refreshing…")
        await query.edit_message_text(
            _format_status(), parse_mode="Markdown", reply_markup=main_menu()
        )
        return

    if data == CONTAINERS:
        await query.answer()
        containers, error = await _safe_containers()
        if error:
            await query.edit_message_text(f"⚠️ {error}", reply_markup=main_menu())
            return
        await query.edit_message_text(
            f"🐳 *Containers* ({len(containers)})\nPilih kontainer untuk detail atau restart.",
            parse_mode="Markdown",
            reply_markup=containers_menu(containers),
        )
        return

    if data.startswith("container:"):
        parts = data.split(":", 2)
        action = parts[1] if len(parts) > 1 else ""
        name = parts[2] if len(parts) > 2 else ""

        if action == "info":
            await query.answer()
            containers, error = await _safe_containers()
            if error:
                await query.edit_message_text(f"⚠️ {error}", reply_markup=main_menu())
                return
            container = next((item for item in containers if item["name"] == name), None)
            if container is None:
                await query.edit_message_text(
                    f"Container *{name}* not found.", parse_mode="Markdown", reply_markup=containers_menu(containers)
                )
                return
            text = (
                f"🐳 *{container['name']}*\n"
                f"Image: `{container['image']}`\n"
                f"ID: `{container['id']}`\n"
                f"State: *{container['state']}*\n"
                f"CPU: {container['cpu_percent']}%\n"
                f"RAM: {container['memory_percent']}%"
            )
            await query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=container_actions(container)
            )
            return

        if action == "restart":
            await query.answer()
            await query.edit_message_text(
                f"⚠️ Restart container *{name}*?",
                parse_mode="Markdown",
                reply_markup=restart_confirmation(name),
            )
            return

        if action == "confirm":
            await query.answer("Restarting…")
            timeout = context.application.bot_data["settings"].docker_restart_timeout
            ok, message = await asyncio.to_thread(restart_container, name, timeout)
            await query.edit_message_text(
                ("✅ " if ok else "❌ ") + message,
                parse_mode="Markdown",
                reply_markup=main_menu(),
            )
            return

    await query.answer("Unknown action.")


@auth_required
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and tell the user something went wrong without leaking details."""
    error = context.error
    print(f"[bot] error: {error!r}")
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Terjadi kesalahan internal. Coba lagi sebentar lagi."
        )


__all__ = [
    "button_handler",
    "containers_command",
    "error_handler",
    "help_command",
    "start",
    "status_command",
]
