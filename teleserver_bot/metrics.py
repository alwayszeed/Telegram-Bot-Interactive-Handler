"""System and container metrics for the Telegram bot (psutil + Docker SDK)."""

from __future__ import annotations

import os
import platform
import socket
import time
from datetime import datetime, timezone

import psutil

try:
    import docker
    from docker.errors import DockerException, NotFound
except ImportError:  # pragma: no cover - optional runtime dependency
    docker = None  # type: ignore[assignment]

    class DockerException(Exception):  # type: ignore[no-redef]
        pass

    class NotFound(DockerException):  # type: ignore[no-redef]
        pass


def _client():
    if docker is None:
        raise RuntimeError("Docker SDK is not installed. Run: pip install docker")
    try:
        return docker.from_env()
    except DockerException as exc:
        raise RuntimeError(f"Cannot connect to Docker daemon: {exc}") from exc


def system_summary() -> dict:
    memory = psutil.virtual_memory()
    disk_path = "C:\\" if os.name == "nt" else "/"
    disk = psutil.disk_usage(disk_path)
    return {
        "hostname": socket.gethostname(),
        "platform": f"{platform.system()} {platform.release()}",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cpu_percent": round(psutil.cpu_percent(interval=0.4), 1),
        "cpu_count": psutil.cpu_count(logical=True) or 1,
        "memory_percent": round(memory.percent, 1),
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_percent": round(disk.percent, 1),
        "disk_used": disk.used,
        "disk_total": disk.total,
        "uptime_seconds": round(time.time() - psutil.boot_time()),
        "load_average": list(os.getloadavg()) if hasattr(os, "getloadavg") else None,
    }


def _cpu_percent(stats: dict) -> float:
    try:
        cpu = stats["cpu_stats"]
        previous = stats["precpu_stats"]
        cpu_delta = cpu["cpu_usage"]["total_usage"] - previous["cpu_usage"]["total_usage"]
        system_delta = cpu["system_cpu_usage"] - previous.get("system_cpu_usage", 0)
        cpus = cpu.get("online_cpus") or 1
        if cpu_delta > 0 and system_delta > 0:
            return round((cpu_delta / system_delta) * cpus * 100.0, 1)
    except (KeyError, TypeError):
        pass
    return 0.0


def _memory_percent(stats: dict) -> float:
    memory = stats.get("memory_stats") or {}
    usage = int(memory.get("usage") or 0)
    limit = int(memory.get("limit") or 0)
    return round((usage / limit) * 100.0, 1) if limit else 0.0


def list_containers() -> list[dict]:
    """Return all containers (running and stopped) with lightweight stats."""
    client = _client()
    items: list[dict] = []
    try:
        for container in client.containers.list(all=True):
            cpu = mem = 0.0
            if container.status == "running":
                try:
                    stats = container.stats(stream=False)
                    cpu = _cpu_percent(stats)
                    mem = _memory_percent(stats)
                except Exception:
                    pass
            items.append(
                {
                    "name": container.name,
                    "id": container.short_id,
                    "image": (container.image.tags or [container.image.short_id])[0],
                    "state": container.status,
                    "cpu_percent": cpu,
                    "memory_percent": mem,
                }
            )
    finally:
        client.close()
    return sorted(items, key=lambda item: item["name"].lower())


def restart_container(name: str, timeout: int = 10) -> tuple[bool, str]:
    """Restart a container by name. Returns (ok, human-readable message)."""
    client = _client()
    try:
        container = client.containers.get(name)
        container.restart(timeout=timeout)
        container.reload()
        return True, f"Container *{name}* restarted (state: {container.status})."
    except NotFound:
        return False, f"Container *{name}* was not found."
    except DockerException as exc:
        return False, f"Failed to restart *{name}*: {exc}"
    finally:
        client.close()


def human_bytes(value: int) -> str:
    value = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} B"


__all__ = ["human_bytes", "list_containers", "restart_container", "system_summary"]
