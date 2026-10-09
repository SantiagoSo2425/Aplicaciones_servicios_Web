"""Schemas Pydantic para sensores (solo lectura)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SensorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    categoria: str
    ubicacion: str
    activo: bool
    fecha_registro: datetime


class SensorOutBogota(SensorOut):
    """Variante con fecha convertida a string Bogota (se construye en la API)."""

    fecha_registro: str
    fecha_registro_utc: Optional[str] = None
