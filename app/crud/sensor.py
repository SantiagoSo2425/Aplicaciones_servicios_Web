"""CRUD de sensores: solo lectura (el catalogo lo suministra el docente)."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def get_all(db: Session) -> List[Sensor]:
    return db.query(Sensor).order_by(Sensor.id).all()


def get_by_id(db: Session, sensor_id: int) -> Optional[Sensor]:
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def get_by_codigo(db: Session, codigo: str) -> Optional[Sensor]:
    return db.query(Sensor).filter(Sensor.codigo == codigo).first()
