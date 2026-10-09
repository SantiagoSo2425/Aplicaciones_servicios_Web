"""Endpoint de detalle de mediciones."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.database.connection import get_db
from app.utils.timezone import to_bogota_iso

router = APIRouter(prefix="/mediciones", tags=["mediciones"])


@router.get("/{medicion_id}", summary="Consultar una medicion por ID")
def por_id(medicion_id: int, db: Session = Depends(get_db)):
    m = crud_medicion.get_by_id(db, medicion_id)
    if not m:
        raise HTTPException(
            status_code=404, detail=f"Medicion con id {medicion_id} no encontrada"
        )
    cfg = m.magnitud_config
    sensor = None
    sensor_codigo = None
    sensor_id = cfg.sensor_id if cfg else None
    if cfg:
        sensor = crud_sensor.get_by_id(db, cfg.sensor_id)
        sensor_codigo = sensor.codigo if sensor else None
    return {
        "id": m.id,
        "sensor_id": sensor_id,
        "sensor_codigo": sensor_codigo,
        "sensor_magnitud_id": m.sensor_magnitud_id,
        "magnitud": cfg.magnitud if cfg else None,
        "unidad": cfg.unidad if cfg else None,
        "valor": float(m.valor),
        "timestamp_utc": to_bogota_iso(m.timestamp_utc),
        "timestamp_utc_original": m.timestamp_utc.isoformat() if m.timestamp_utc else None,
        "fecha_recepcion": to_bogota_iso(m.fecha_recepcion) if m.fecha_recepcion else None,
    }
