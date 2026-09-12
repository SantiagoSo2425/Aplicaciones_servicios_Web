"""Validación local de registros ya normalizados contra las reglas de
negocio definidas en CONTRATO_API.md.

Un registro puede estar correctamente tipado (normalizado) pero aun así
violar una restricción del contrato (rango, campo vacío, etc.). Esta etapa
identifica esos casos como 'rechazado_localmente'.
"""

from __future__ import annotations

from typing import Any

from normalizacion import ORIGENES_VALIDOS


def validar_registro(medicion: dict[str, Any]) -> list[str]:
    """Retorna la lista de violaciones al contrato encontradas.

    Una lista vacía significa que el registro es válido localmente.
    """
    errores: list[str] = []

    if not medicion.get("ciudad", "").strip():
        errores.append("ciudad vacía")

    if not medicion.get("pais", "").strip():
        errores.append("pais vacío")

    latitud = medicion.get("latitud")
    if not (-90 <= latitud <= 90):
        errores.append(f"latitud fuera de rango: {latitud}")

    longitud = medicion.get("longitud")
    if not (-180 <= longitud <= 180):
        errores.append(f"longitud fuera de rango: {longitud}")

    humedad = medicion.get("humedad")
    if not (0 <= humedad <= 100):
        errores.append(f"humedad fuera de rango: {humedad}")

    viento_kmh = medicion.get("viento_kmh")
    if viento_kmh < 0:
        errores.append(f"viento_kmh negativo: {viento_kmh}")

    if medicion.get("origen") not in ORIGENES_VALIDOS:
        errores.append(f"origen no permitido: {medicion.get('origen')!r}")

    return errores
