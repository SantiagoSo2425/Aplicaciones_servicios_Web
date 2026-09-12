"""Construcción del reporte final de la integración.

Agrega los contadores exigidos por el taller y conserva, para cada
registro, su trazabilidad (id de origen, etapa alcanzada y resultado).
"""

from __future__ import annotations

from typing import Any


def construir_reporte(seguimiento: list[dict[str, Any]], resultado_consulta: Any) -> dict[str, Any]:
    """seguimiento: lista de dicts con al menos las claves
    'id_trazabilidad', 'origen_dataset', 'etapa', 'detalle'.
    """
    conteo = {
        "procesados": len(seguimiento),
        "normalizados": 0,
        "errores_normalizacion": 0,
        "validos_localmente": 0,
        "rechazados_localmente": 0,
        "enviados": 0,
        "aceptados_api": 0,
        "rechazados_api": 0,
        "errores_comunicacion": 0,
    }

    for item in seguimiento:
        etapa = item["etapa"]
        if etapa == "error_normalizacion":
            conteo["errores_normalizacion"] += 1
            continue

        conteo["normalizados"] += 1

        if etapa == "rechazado_localmente":
            conteo["rechazados_localmente"] += 1
            continue

        conteo["validos_localmente"] += 1

        if etapa in ("aceptado_api", "rechazado_api", "error_comunicacion"):
            conteo["enviados"] += 1
        if etapa == "aceptado_api":
            conteo["aceptados_api"] += 1
        elif etapa == "rechazado_api":
            conteo["rechazados_api"] += 1
        elif etapa == "error_comunicacion":
            conteo["errores_comunicacion"] += 1

    return {
        "resumen": conteo,
        "consulta_final": resultado_consulta,
        "registros": seguimiento,
    }
