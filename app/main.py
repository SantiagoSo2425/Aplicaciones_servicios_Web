"""API IoT Taller 2: FastAPI + MQTT + PostgreSQL."""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("app")

# Registrar modelos para que Base conozca las tablas
import app.models.medicion  # noqa: F401
import app.models.sensor  # noqa: F401
import app.models.sensor_magnitud  # noqa: F401
from app.api import medicion as api_medicion
from app.api import sensor as api_sensor
from app.api import sensor_magnitud as api_sm


@asynccontextmanager
async def lifespan(app: FastAPI):
    enable = os.getenv("ENABLE_MQTT", "true").lower() in ("1", "true", "yes")
    if enable:
        try:
            from app.mqtt.client import start_mqtt_background

            start_mqtt_background()
            logger.info("Consumidor MQTT iniciado en background")
        except Exception as exc:
            logger.exception("No se pudo iniciar MQTT: %s", exc)
    else:
        logger.info("ENABLE_MQTT=false, consumidor MQTT desactivado")
    yield
    try:
        from app.mqtt.client import stop_mqtt

        stop_mqtt()
    except Exception:
        pass


app = FastAPI(
    title="Taller 2 - API IoT",
    description="Adquisicion (MQTT), validacion (Pydantic+ORM) y consulta (FastAPI) de datos IoT.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_sensor.router)
app.include_router(api_sm.router)
app.include_router(api_medicion.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "taller-2-iot-api"}


@app.get("/health", tags=["health"])
def health():
    from sqlalchemy import text

    from app.database.connection import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db = "up"
    except Exception as exc:
        db = f"down: {exc}"
    return {"api": "up", "db": db}
