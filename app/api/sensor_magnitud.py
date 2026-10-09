"""Endpoint de detalle de sensor_magnitudes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import sensor_magnitud as crud_sm
from app.database.connection import get_db

router = APIRouter(prefix="/sensor-magnitudes", tags=["sensor-magnitudes"])


@router.get("/{magnitud_id}", summary="Consultar una magnitud configurada por ID")
def por_id(magnitud_id: int, db: Session = Depends(get_db)):
    m = crud_sm.get_by_id(db, magnitud_id)
    if not m:
        raise HTTPException(
            status_code=404,
            detail=f"Sensor-magnitud con id {magnitud_id} no encontrada",
        )
    return {
        "id": m.id,
        "sensor_id": m.sensor_id,
        "magnitud": m.magnitud,
        "unidad": m.unidad,
        "valor_minimo": float(m.valor_minimo),
        "valor_maximo": float(m.valor_maximo),
    }
