"""Colecta datos reales del topico asignado durante N minutos.

Uso:
    python scripts/colectar_20min.py --minutos 20

Guarda log en evidencias/colecta_20min.log con conteo de recibidos/almacenados/rechazados.
Requiere .env con MQTT_TOPIC del sensor asignado.
La API debe estar corriendo aparte o este script usa process_payload directamente.
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

import paho.mqtt.client as mqtt  # noqa: E402

BROKER = os.getenv("MQTT_BROKER", "emqx.coriotlab.co")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data")
USERNAME = os.getenv("MQTT_USERNAME") or None
PASSWORD = os.getenv("MQTT_PASSWORD") or None

stats = Counter(recibidos=0, almacenados=0, rechazados=0)
inicio = datetime.now(timezone.utc)


def on_connect(c, u, f, rc, props=None):
    print(f"Conectado {rc}, suscribiendo a {TOPIC}")
    c.subscribe(TOPIC)


def on_message(c, u, m):
    from app.database.connection import SessionLocal
    from app.mqtt.processor import process_payload

    stats["recibidos"] += 1
    try:
        payload = json.loads(m.payload.decode())
    except Exception as e:
        stats["rechazados"] += 1
        print(f"[RECHAZADO no-JSON] {e}")
        return
    db = SessionLocal()
    try:
        ok, motivo = process_payload(db, payload)
        stats["almacenados" if ok else "rechazados"] += 1
        print(f"[{'OK' if ok else 'RECHAZADO'}] {payload.get('timestamp')} :: {motivo}")
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutos", type=float, default=20)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO)
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if USERNAME:
        c.username_pw_set(USERNAME, PASSWORD or "")
    c.on_connect = on_connect
    c.on_message = on_message
    c.connect(BROKER, PORT, 60)
    c.loop_start()
    fin = time.time() + args.minutos * 60
    print(f"Colectando {args.minutos} min desde {TOPIC} ... (Ctrl+C para detener)")
    try:
        while time.time() < fin:
            time.sleep(5)
            elapsed = (datetime.now(timezone.utc) - inicio).total_seconds() / 60
            print(f"[{elapsed:.1f} min] {dict(stats)}")
    except KeyboardInterrupt:
        print("Detenido por usuario")
    finally:
        c.loop_stop()
        c.disconnect()

    out = Path(__file__).resolve().parents[1] / "evidencias" / "colecta_20min.log"
    out.parent.mkdir(exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"\n=== Colecta {inicio.isoformat()} topic={TOPIC} minutos={args.minutos} stats={dict(stats)} ===\n")
    print(f"Stats finales: {dict(stats)} -> log en {out}")


if __name__ == "__main__":
    main()
