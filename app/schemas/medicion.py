"""Schemas Pydantic para mediciones (lectura + validacion MQTT)."""

from typing import Annotated, Dict, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
)

StrictNumber = Annotated[Union[StrictInt, StrictFloat], Field(description="Valor numerico estricto")]


class MeasurementItem(BaseModel):
    """Una magnitud individual dentro del payload MQTT.

    value es estricto: NO acepta strings numericos como "1795.39".
    """

    model_config = ConfigDict(extra="forbid")

    value: StrictNumber
    unit: str


class MqttPayload(BaseModel):
    """Payload publicado por el sensor en el topico MQTT."""

    model_config = ConfigDict(extra="forbid")

    sensor_id: str = Field(min_length=1, max_length=20)
    timestamp: str = Field(min_length=1)
    measurements: Dict[str, MeasurementItem] = Field(min_length=1)

    @field_validator("sensor_id")
    @classmethod
    def sensor_id_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("sensor_id no puede estar vacio")
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def timestamp_formato(cls, v: str) -> str:
        from datetime import datetime

        text = v.strip()
        probe = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            dt = datetime.fromisoformat(probe)
        except ValueError as exc:
            raise ValueError(f"timestamp con formato invalido: {v}") from exc
        if dt.tzinfo is None:
            raise ValueError("timestamp debe incluir zona horaria (ej. sufijo Z)")
        return v


class MedicionOut(BaseModel):
    """Respuesta GET de una medicion con timestamps en hora de Colombia."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: int
    sensor_codigo: str
    sensor_magnitud_id: int
    magnitud: str
    unidad: str
    valor: float
    timestamp_utc: str
    fecha_recepcion: Optional[str] = None
