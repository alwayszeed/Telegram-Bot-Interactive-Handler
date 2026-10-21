# Telegram Bot Interactive Handler

> Bagian dari seri **Teleserver Pulse** — **Day 6** (kontrol server via Telegram).

Bot Telegram interaktif untuk memantau status server **real-time**, melihat daftar kontainer Docker, dan **me-restart kontainer** menggunakan **inline keyboard**. Akses dibatasi dengan middleware autentikasi berbasis daftar **Telegram user ID**.

## Fitur

- `/start`, `/status`, `/containers`, `/help`.
- Inline keyboard: **Status**, **Containers**, **Refresh**, **Help**.
- Detail kontainer + tombol **Restart** dengan konfirmasi dua langkah.
- Autentikasi: hanya `TELEGRAM_ALLOWED_USER_IDS` yang bisa memakai bot; user lain mendapat pesan penolakan.
- Error handling: kegagalan Docker/daemon ditampilkan sebagai pesan ramah, bukan crash.
- Restart dijalankan di thread terpisah (`asyncio.to_thread`) agar event loop bot tidak blocking.

## Struktur

```
teleserver_bot/
  main.py       # ApplicationBuilder + handler registration
  handlers.py   # command & callback handlers
  auth.py       # auth_required middleware
  keyboards.py  # inline keyboard layouts
  metrics.py    # psutil + Docker SDK (status, list, restart)
  config.py     # environment settings
tests/
  test_auth_and_keyboards.py
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Isi `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_ALLOWED_USER_IDS=111111111,222222222
DOCKER_RESTART_TIMEOUT=10
```

Dapatkan user ID Anda via [@userinfobot](https://t.me/userinfobot). Token bot dari [@BotFather](https://t.me/BotFather).

## Menjalankan

```bash
python -m teleserver_bot
```

## Alur inline keyboard

```
/start
  └─ 📊 Status          → CPU/RAM/disk real-time
  └─ 🐳 Containers      → daftar kontainer
        └─ pilih kontainer → detail + 🔁 Restart
              └─ konfirmasi → ✅ restart / ✖️ cancel
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Seri Teleserver Pulse

| Hari | Fokus | Repo |
|------|-------|------|
| Day 5 | System metrics collector (psutil + Docker SDK) | [System Metrics Collector](https://github.com/alwayszeed/System-Metrics-Collector) |
| Day 6 | Telegram bot: inline keyboard, restart, auth | **repo ini** |
| Day 7 | Auto-alerting >85% + time-series logger | [Auto-Alerting & Time-Series Logger](https://github.com/alwayszeed/Auto-Alerting-Time-Series-Logger) |
