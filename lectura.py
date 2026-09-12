"""Lectura de los datasets originales de los proveedores.

Cada función retorna una lista de registros "crudos" envueltos con un
identificador de trazabilidad y el nombre del dataset de origen. No se
realiza ninguna transformación de contenido en este módulo: solo lectura
y manejo de errores de acceso/parseo del archivo.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class RegistroCrudo:
    """Un registro tal como fue leído de la fuente, antes de normalizar."""

    def __init__(self, id_trazabilidad: str, origen_dataset: str, datos: dict[str, Any]):
        self.id_trazabilidad = id_trazabilidad
        self.origen_dataset = origen_dataset
        self.datos = datos


def leer_proveedor_a(ruta: Path) -> list[RegistroCrudo]:
    """Lee el archivo JSON del proveedor A.

    Lanza FileNotFoundError o json.JSONDecodeError si el archivo no existe
    o no es interpretable; estos casos deben ser manejados por el llamador.
    """
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = json.load(f)

    registros = contenido.get("records", [])
    resultado = []
    for i, registro in enumerate(registros):
        rid = registro.get("provider_record_id") or f"A-sin-id-{i}"
        resultado.append(RegistroCrudo(rid, "proveedor_a", registro))
    return resultado


def leer_proveedor_b(ruta: Path) -> tuple[list[RegistroCrudo], list[dict[str, Any]]]:
    """Lee el archivo CSV del proveedor B (delimitado por ';').

    Retorna una tupla (registros_validos, filas_defectuosas). Una fila se
    considera defectuosa cuando el número de columnas no coincide con el
    encabezado (columnas de más o de menos).
    """
    registros: list[RegistroCrudo] = []
    defectuosas: list[dict[str, Any]] = []

    with open(ruta, "r", encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f, delimiter=";")
        for i, fila in enumerate(lector):
            rid = fila.get("record_code") or f"B-sin-id-{i}"

            columnas_extra = fila.get(None)
            columnas_faltantes = any(v is None for k, v in fila.items() if k is not None)

            if columnas_extra or columnas_faltantes:
                defectuosas.append({"posicion": i, "id_trazabilidad": rid, "fila": fila})
                continue

            registros.append(RegistroCrudo(rid, "proveedor_b", dict(fila)))

    return registros, defectuosas
