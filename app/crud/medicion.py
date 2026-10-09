"""CRUD de mediciones: crear + leer con filtros."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.models.medicion import Medicion
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud


def create_many(
    db: Session,
    items: List[dict],
) -> List[Medicion]:
    """Crea varias mediciones del mismo payload (mismo timestamp_utc)."""
    objs = [Medicion(**data) for data in items]
    db.add_all(objs)
    db.commit()
    for obj in objs:
        db.refresh(obj)
    return objs


def get_by_id(db: Session, medicion_id: int) -> Optional[Medicion]:
    return (
        db.query(Medicion)
        .options(joinedload(Medicion.magnitud_config))
        .filter(Medicion.id == medicion_id)
        .first()
    )


def _base_query_sensor(db: Session, sensor_id: int):
    return (
        db.query(Medicion)
        .join(SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id)
        .join(Sensor, SensorMagnitud.sensor_id == Sensor.id)
        .options(joinedload(Medicion.magnitud_config))
        .filter(Sensor.id == sensor_id)
    )


def list_by_sensor(
    db: Session,
    sensor_id: int,
    magnitud: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[Medicion]:
    q = _base_query_sensor(db, sensor_id)
    if magnitud:
        q = q.filter(SensorMagnitud.magnitud == magnitud)
    if desde:
        q = q.filter(Medicion.timestamp_utc >= desde)
    if hasta:
        q = q.filter(Medicion.timestamp_utc <= hasta)
    q = q.order_by(desc(Medicion.timestamp_utc), desc(Medicion.id))
    if limit:
        q = q.limit(limit)
    return q.all()


def get_last_by_sensor(db: Session, sensor_id: int) -> List[Medicion]:
    """Ultima medicion: todas las magnitudes del timestamp mas reciente."""
    rows = list_by_sensor(db, sensor_id, limit=None)
    if not rows:
        return []
    max_ts = rows[0].timestamp_utc
    return [r for r in rows if r.timestamp_utc == max_ts]


def count_all(db: Session) -> int:
    return db.query(Medicion).count()
