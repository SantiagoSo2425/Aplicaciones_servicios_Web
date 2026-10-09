"""Modelo ORM de la tabla sensor_magnitudes."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class SensorMagnitud(Base):
    __tablename__ = "sensor_magnitudes"
    __table_args__ = (
        UniqueConstraint("sensor_id", "magnitud", name="uq_sensor_magnitud"),
        CheckConstraint(
            "valor_minimo < valor_maximo", name="ck_rango_valores"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(
        Integer,
        ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    magnitud = Column(String(50), nullable=False)
    unidad = Column(String(20), nullable=False)
    valor_minimo = Column(Numeric(12, 4), nullable=False)
    valor_maximo = Column(Numeric(12, 4), nullable=False)

    sensor = relationship("Sensor", back_populates="magnitudes")
    mediciones = relationship(
        "Medicion", back_populates="magnitud_config", cascade="save-update, merge"
    )
