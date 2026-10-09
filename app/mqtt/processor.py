"""Procesamiento y validacion de payloads MQTT.

Pipeline:
1. Pydantic (estructura, tipos estrictos, timestamp con zona).
2. ORM + negocio (sensor existe/activo, magnitud configurada, unidad, rango).
3. Si TODO es valido -> N filas en mediciones con mismo timestamp_utc.
   Si ALGO falla -> 0 filas (rechazo total del payload).
"""

import logging
from datetime import datetime, timezone
from typing import Tuple

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sm
from app.schemas.medicion import MqttPayload

logger = logging.getLogger("mqtt.processor")


def _parse_timestamp_utc(raw: str) -> datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def process_payload(db: Session, payload: dict) -> Tuple[bool, str]:
    """Valida y almacena un payload MQTT.

    Returns:
        (True, mensaje) si se almaceno; (False, motivo) si se rechazo.
    """
    # --- 1. Pydantic ---
    try:
        data = MqttPayload.model_validate(payload)
    except ValidationError as exc:
        motivo = f"Pydantic: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}"
        logger.warning("Rechazado %s | %s", payload, motivo)
        return False, motivo

    # --- 2a. Timestamp ---
    try:
        ts_utc = _parse_timestamp_utc(data.timestamp)
    except Exception as exc:
        motivo = f"Timestamp invalido: {exc}"
        logger.warning("Rechazado %s | %s", payload, motivo)
        return False, motivo

    # --- 2b. Sensor existe y activo ---
    sensor = crud_sensor.get_by_codigo(db, data.sensor_id)
    if sensor is None:
        motivo = f"Sensor inexistente: codigo '{data.sensor_id}' no esta en catalogo"
        logger.warning("Rechazado | %s", motivo)
        return False, motivo
    if not sensor.activo:
        motivo = f"Sensor '{data.sensor_id}' esta inactivo"
        logger.warning("Rechazado | %s", motivo)
        return False, motivo

    # --- 2c. Magnitud / unidad / rango (todas deben pasar) ---
    pendientes = []
    for nombre_mag, item in data.measurements.items():
        cfg = crud_sm.get_by_sensor_and_magnitud(db, sensor.id, nombre_mag)
        if cfg is None:
            motivo = f"Magnitud incorrecta: '{nombre_mag}' no configurada para {sensor.codigo}"
            logger.warning("Rechazado | %s", motivo)
            return False, motivo
        if item.unit != cfg.unidad:
            motivo = (
                f"Unidad incorrecta: '{nombre_mag}' trae '{item.unit}' "
                f"pero se espera '{cfg.unidad}'"
            )
            logger.warning("Rechazado | %s", motivo)
            return False, motivo
        try:
            valor = float(item.value)
        except (TypeError, ValueError):
            motivo = f"Tipo de dato incorrecto: '{nombre_mag}.value' no es numerico"
            logger.warning("Rechazado | %s", motivo)
            return False, motivo
        vmin, vmax = float(cfg.valor_minimo), float(cfg.valor_maximo)
        if not (vmin <= valor <= vmax):
            motivo = (
                f"Valor fuera de rango: '{nombre_mag}'={valor} "
                f"fuera de [{vmin}, {vmax}]"
            )
            logger.warning("Rechazado | %s", motivo)
            return False, motivo
        pendientes.append(
            {
                "sensor_magnitud_id": cfg.id,
                "valor": valor,
                "timestamp_utc": ts_utc,
            }
        )

    # --- 3. Almacenar (una fila por magnitud, mismo timestamp) ---
    try:
        objs = crud_medicion.create_many(db, pendientes)
    except Exception as exc:
        db.rollback()
        motivo = f"Error DB al almacenar: {exc}"
        logger.exception(motivo)
        return False, motivo

    logger.info(
        "Almacenado sensor=%s ts=%s filas=%s",
        sensor.codigo,
        ts_utc.isoformat(),
        len(objs),
    )
    return True, f"Almacenadas {len(objs)} mediciones de {sensor.codigo}"
