"""Transformación de registros crudos al contrato institucional.

Un registro se considera con "error de normalización" cuando algún dato no
puede convertirse al tipo o representación exigida por el contrato
(por ejemplo, una temperatura no numérica o una fecha ilegible). La
ausencia total de un valor requerido se trata de la misma forma: no hay
nada que convertir.

En cambio, un valor presente y del tipo correcto pero fuera de las reglas
de negocio (ciudad vacía, humedad fuera de rango, etc.) SÍ se normaliza
correctamente; su evaluación corresponde a la etapa de validación local.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from lectura import RegistroCrudo

ORIGENES_VALIDOS = {"proveedor_a", "proveedor_b"}

# Proveedor B no incluye zona horaria; se asume la misma zona usada por el
# proveedor A en los datos suministrados (UTC-05:00, hora de Colombia).
ZONA_HORARIA_PROVEEDOR_B = timezone(timedelta(hours=-5))


class ErrorNormalizacion(Exception):
    """Señala que un registro no puede convertirse al contrato institucional."""


def _a_numero(valor: Any) -> float:
    if valor is None:
        raise ErrorNormalizacion("valor numérico ausente")
    if isinstance(valor, bool):
        raise ErrorNormalizacion(f"valor no numérico: {valor!r}")
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        return float(str(valor).strip())
    except (ValueError, TypeError):
        raise ErrorNormalizacion(f"valor no numérico: {valor!r}")


def _fahrenheit_a_celsius(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def _ms_a_kmh(ms: float) -> float:
    return ms * 3.6


def _fecha_iso_desde_iso(valor: Any) -> str:
    if not valor or not isinstance(valor, str):
        raise ErrorNormalizacion("fecha/hora ausente")
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        raise ErrorNormalizacion(f"fecha/hora no interpretable: {valor!r}")
    return dt.isoformat()


def _fecha_iso_desde_formato_b(valor: Any) -> str:
    if not valor or not isinstance(valor, str) or not valor.strip():
        raise ErrorNormalizacion("fecha/hora ausente")
    try:
        dt = datetime.strptime(valor.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ErrorNormalizacion(f"fecha/hora no interpretable: {valor!r}")
    dt = dt.replace(tzinfo=ZONA_HORARIA_PROVEEDOR_B)
    return dt.isoformat()


def normalizar_registro_a(registro: RegistroCrudo) -> dict[str, Any]:
    """Convierte un registro del proveedor A al contrato institucional.

    Lanza ErrorNormalizacion si algún dato no puede convertirse.
    """
    datos = registro.datos
    estacion = datos.get("station") or {}
    ubicacion = datos.get("location") or {}
    mediciones = datos.get("measurements") or {}

    ciudad = estacion.get("city_name")
    if ciudad is None:
        raise ErrorNormalizacion("ciudad ausente")

    pais = estacion.get("country_code")
    if pais is None:
        pais = ""

    latitud = _a_numero(ubicacion.get("lat"))
    longitud = _a_numero(ubicacion.get("lon"))
    temperatura_c = _fahrenheit_a_celsius(_a_numero(mediciones.get("temperature_f")))
    humedad = _a_numero(mediciones.get("relative_humidity"))
    viento_kmh = _ms_a_kmh(_a_numero(mediciones.get("wind_speed_ms")))
    fecha_hora = _fecha_iso_desde_iso(datos.get("observed_at"))

    return {
        "ciudad": str(ciudad),
        "pais": str(pais),
        "latitud": latitud,
        "longitud": longitud,
        "temperatura_c": temperatura_c,
        "humedad": humedad,
        "viento_kmh": viento_kmh,
        "fecha_hora": fecha_hora,
        "origen": "proveedor_a",
    }


def normalizar_registro_b(registro: RegistroCrudo) -> dict[str, Any]:
    """Convierte un registro del proveedor B al contrato institucional.

    Lanza ErrorNormalizacion si algún dato no puede convertirse.
    """
    datos = registro.datos

    ciudad = datos.get("municipality")
    if ciudad is None:
        raise ErrorNormalizacion("ciudad ausente")

    pais = datos.get("country")
    if pais is None:
        pais = ""

    latitud = _a_numero(datos.get("latitude_deg"))
    longitud = _a_numero(datos.get("longitude_deg"))
    temperatura_c = _a_numero(datos.get("temp_celsius"))
    humedad = _a_numero(datos.get("humidity_pct"))
    viento_kmh = _a_numero(datos.get("wind_kmh"))
    fecha_hora = _fecha_iso_desde_formato_b(datos.get("measurement_time"))

    return {
        "ciudad": str(ciudad),
        "pais": str(pais),
        "latitud": latitud,
        "longitud": longitud,
        "temperatura_c": temperatura_c,
        "humedad": humedad,
        "viento_kmh": viento_kmh,
        "fecha_hora": fecha_hora,
        "origen": "proveedor_b",
    }


def normalizar_registro(registro: RegistroCrudo) -> dict[str, Any]:
    """Despacha la normalización según el dataset de origen del registro."""
    if registro.origen_dataset == "proveedor_a":
        return normalizar_registro_a(registro)
    if registro.origen_dataset == "proveedor_b":
        return normalizar_registro_b(registro)
    raise ErrorNormalizacion(f"origen de dataset desconocido: {registro.origen_dataset!r}")
