"""Cliente MQTT suscriptor: conecta, escucha el topico y delega a processor."""

import json
import logging
import os
import threading
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mqtt.client")

BROKER = os.getenv("MQTT_BROKER", "emqx.coriotlab.co")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data")
USERNAME = os.getenv("MQTT_USERNAME") or None
PASSWORD = os.getenv("MQTT_PASSWORD") or None
KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))

_client: mqtt.Client | None = None
_thread: threading.Thread | None = None


def _on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code != 0:
        logger.error("Error conexion MQTT: %s", reason_code)
        return
    logger.info("Conectado a %s:%s", BROKER, PORT)
    result, _ = client.subscribe(TOPIC)
    if result != mqtt.MQTT_ERR_SUCCESS:
        logger.error("No fue posible suscribirse a %s: %s", TOPIC, result)
        return
    logger.info("Suscrito a %s", TOPIC)


def _on_message(client, userdata, message):
    received_at = datetime.now(timezone.utc).isoformat()
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        logger.warning("[%s] Payload no-JSON en %s: %s", received_at, message.topic, error)
        return

    # Import diferido para evitar circulos y abaratar import en tests
    from app.database.connection import SessionLocal
    from app.mqtt.processor import process_payload

    db = SessionLocal()
    try:
        ok, motivo = process_payload(db, payload)
        estado = "OK-ALMACENADO" if ok else "RECHAZADO"
        logger.info("[%s] %s topic=%s motivo=%s", received_at, estado, message.topic, motivo)
        print(f"[{received_at}] {estado} {message.topic} :: {motivo}", flush=True)
    finally:
        db.close()


def start_mqtt_background() -> mqtt.Client:
    """Inicia el loop MQTT en un hilo daemon y retorna el cliente."""
    global _client
    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USERNAME:
        _client.username_pw_set(USERNAME, PASSWORD or "")
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    logger.info("Conectando a %s:%s topic=%s ...", BROKER, PORT, TOPIC)
    _client.connect(BROKER, PORT, KEEPALIVE)
    _client.loop_start()
    return _client


def stop_mqtt():
    global _client
    if _client is not None:
        try:
            _client.loop_stop()
            _client.disconnect()
        except Exception:
            pass
        _client = None


def run_forever():
    """Entry-point para correr solo el consumidor (sin API)."""
    logging.basicConfig(level=logging.INFO)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USERNAME:
        c.username_pw_set(USERNAME, PASSWORD or "")
    c.on_connect = _on_connect
    c.on_message = _on_message
    print(f"Conectando a {BROKER}:{PORT} topic={TOPIC} ...")
    c.connect(BROKER, PORT, KEEPALIVE)
    c.loop_forever()
