"""Utilidades de zona horaria: UTC -> America/Bogota."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")


def ensure_aware_utc(dt: datetime) -> datetime:
    """Garantiza un datetime consciente en UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_bogota_iso(dt: datetime) -> str:
    """Convierte un datetime UTC a ISO-8601 en hora local de Colombia.

    Formato legible y consistente, ej: 2026-10-08T15:57:41-05:00
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BOGOTA_TZ).isoformat()


def parse_filtro_fecha(value: str) -> datetime:
    """Parsea un filtro de fecha de query param a datetime consciente UTC.

    Acepta ISO-8601 con o sin zona. Si no trae zona se asume UTC.
    Lanza ValueError si el formato es invalido.
    """
    if value is None:
        return None
    text = value.strip()
    # Soportar sufijo Z
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Formato de fecha invalido: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
