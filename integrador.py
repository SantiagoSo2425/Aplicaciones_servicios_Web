"""Cliente integrador — Taller 1.

Lee los datasets de los proveedores, los normaliza al contrato
institucional, los valida localmente, envía las mediciones válidas a la
API, consulta lo registrado y genera las evidencias en salida/.

Uso:
    python integrador.py
"""

from __future__ import annotations

import json
from pathlib import Path

from cliente_api import ClienteApiInstitucional
from lectura import leer_proveedor_a, leer_proveedor_b
from normalizacion import ErrorNormalizacion, normalizar_registro
from reporte import construir_reporte
from validacion import validar_registro

# --- Configuración del equipo (ajustar con los datos suministrados) ---
URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-10-APPSWEB"
# -----------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
RUTA_PROVEEDOR_A = BASE_DIR / "datos" / "proveedor_a.json"
RUTA_PROVEEDOR_B = BASE_DIR / "datos" / "proveedor_b.csv"
DIR_SALIDA = BASE_DIR / "salida"


def _leer_datasets() -> list:
    """Lee ambos datasets, manejando errores de acceso/parseo sin abortar."""
    registros = []

    try:
        registros.extend(leer_proveedor_a(RUTA_PROVEEDOR_A))
    except FileNotFoundError:
        print(f"[ADVERTENCIA] No se encontró {RUTA_PROVEEDOR_A}")
    except json.JSONDecodeError as exc:
        print(f"[ADVERTENCIA] {RUTA_PROVEEDOR_A} no es un JSON válido: {exc}")

    try:
        registros_b, defectuosas = leer_proveedor_b(RUTA_PROVEEDOR_B)
        registros.extend(registros_b)
        for fila in defectuosas:
            print(f"[ADVERTENCIA] Fila CSV defectuosa: {fila['id_trazabilidad']}")
    except FileNotFoundError:
        print(f"[ADVERTENCIA] No se encontró {RUTA_PROVEEDOR_B}")

    return registros


def _procesar(registros: list) -> tuple[list[dict], list[dict], list[tuple[dict, dict]]]:
    """Normaliza y valida cada registro.

    Retorna (mediciones_para_enviar, seguimiento) donde seguimiento
    contiene un ítem por cada registro leído, con su etapa alcanzada.
    """
    normalizadas: list[dict] = []
    seguimiento: list[dict] = []
    pendientes_de_envio: list[tuple[dict, dict]] = []  # (medicion, item_seguimiento)

    for registro in registros:
        item = {
            "id_trazabilidad": registro.id_trazabilidad,
            "origen_dataset": registro.origen_dataset,
        }

        try:
            medicion = normalizar_registro(registro)
        except ErrorNormalizacion as exc:
            item["etapa"] = "error_normalizacion"
            item["detalle"] = str(exc)
            seguimiento.append(item)
            continue

        errores = validar_registro(medicion)
        entrada_normalizada = {
            "id_trazabilidad": registro.id_trazabilidad,
            "origen_dataset": registro.origen_dataset,
            "medicion": medicion,
            "valido_localmente": not errores,
            "errores_validacion": errores,
        }
        normalizadas.append(entrada_normalizada)

        if errores:
            item["etapa"] = "rechazado_localmente"
            item["detalle"] = errores
            seguimiento.append(item)
            continue

        pendientes_de_envio.append((medicion, item))

    return normalizadas, seguimiento, pendientes_de_envio


def _enviar_mediciones(cliente: ClienteApiInstitucional, pendientes: list[tuple[dict, dict]], seguimiento: list[dict]) -> None:
    for medicion, item in pendientes:
        resultado = cliente.enviar_medicion(medicion)

        if resultado.estado == "aceptado":
            item["etapa"] = "aceptado_api"
        elif resultado.estado == "rechazado":
            item["etapa"] = "rechazado_api"
        else:
            item["etapa"] = "error_comunicacion"

        item["detalle"] = {
            "http_status": resultado.http_status,
            "intentos": resultado.intentos,
            "cuerpo_respuesta": resultado.cuerpo_respuesta,
            "error": resultado.detalle,
        }
        seguimiento.append(item)


def main() -> None:
    DIR_SALIDA.mkdir(exist_ok=True)

    registros = _leer_datasets()
    normalizadas, seguimiento, pendientes = _procesar(registros)

    with open(DIR_SALIDA / "normalizadas.json", "w", encoding="utf-8") as f:
        json.dump(normalizadas, f, ensure_ascii=False, indent=2)

    cliente = ClienteApiInstitucional(URL_BASE, EQUIPO)
    _enviar_mediciones(cliente, pendientes, seguimiento)

    resultado_consulta = cliente.consultar_mediciones()
    consulta_final = {
        "estado": resultado_consulta.estado,
        "http_status": resultado_consulta.http_status,
        "cuerpo_respuesta": resultado_consulta.cuerpo_respuesta,
        "error": resultado_consulta.detalle,
    }

    reporte = construir_reporte(seguimiento, consulta_final)

    with open(DIR_SALIDA / "reporte.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    resumen = reporte["resumen"]
    print("Integración completada.")
    for clave, valor in resumen.items():
        print(f"  {clave}: {valor}")


if __name__ == "__main__":
    main()
