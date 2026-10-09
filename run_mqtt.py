"""Permite ejecutar solo el consumidor MQTT: python -m app.mqtt.client"""

from app.mqtt.client import run_forever

if __name__ == "__main__":
    run_forever()
