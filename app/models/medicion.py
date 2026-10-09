"""Modelo ORM de la tabla mediciones."""

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    sensor_magnitud_id = Column(
        Integer,
        ForeignKey("sensor_magnitudes.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    valor = Column(Numeric(12, 4), nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    fecha_recepcion = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    magnitud_config = relationship("SensorMagnitud", back_populates="mediciones")
