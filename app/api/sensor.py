"""Endpoints de sensores y consultas historicas."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sm
from app.database.connection import get_db
from app.utils.timezone import parse_filtro_fecha, to_bogota_iso

router = APIRouter(prefix="/sensores", tags=["sensores"])


def _sensor_out(s) -> dict:
    return {
        "id": s.id,
        "codigo": s.codigo,
        "nombre": s.nombre,
        "categoria": s.categoria,
        "ubicacion": s.ubicacion,
        "activo": s.activo,
        "fecha_registro": to_bogota_iso(s.fecha_registro),
        "fecha_registro_utc": s.fecha_registro.isoformat() if s.fecha_registro else None,
    }


def _medicion_out(m) -> dict:
    cfg = m.magnitud_config
    sensor_codigo = getattr(getattr(cfg, "sensor", None), "codigo", None)
    # Si la relacion sensor no esta cargada, buscar via sensor_id del config
    return {
        "id": m.id,
        "sensor_id": cfg.sensor_id if cfg else None,
        "sensor_codigo": sensor_codigo,
        "sensor_magnitud_id": m.sensor_magnitud_id,
        "magnitud": cfg.magnitud if cfg else None,
        "unidad": cfg.unidad if cfg else None,
        "valor": float(m.valor),
        "timestamp_utc": to_bogota_iso(m.timestamp_utc),
        "timestamp_utc_original": m.timestamp_utc.isoformat() if m.timestamp_utc else None,
        "fecha_recepcion": to_bogota_iso(m.fecha_recepcion) if m.fecha_recepcion else None,
    }


@router.get("", summary="Listar todos los sensores")
def listar_sensores(db: Session = Depends(get_db)):
    sensores = crud_sensor.get_all(db)
    return [_sensor_out(s) for s in sensores]


@router.get("/por-codigo/{codigo}", summary="Buscar sensor por codigo (ej. AQ-001)")
def por_codigo(codigo: str, db: Session = Depends(get_db)):
    s = crud_sensor.get_by_codigo(db, codigo)
    if not s:
        raise HTTPException(status_code=404, detail=f"Sensor con codigo '{codigo}' no encontrado")
    return _sensor_out(s)


@router.get("/{sensor_id}", summary="Consultar sensor por ID numerico")
def por_id(sensor_id: int, db: Session = Depends(get_db)):
    s = crud_sensor.get_by_id(db, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Sensor con id {sensor_id} no encontrado")
    return _sensor_out(s)


@router.get("/{sensor_id}/magnitudes", summary="Magnitudes configuradas de un sensor")
def magnitudes_de_sensor(sensor_id: int, db: Session = Depends(get_db)):
    s = crud_sensor.get_by_id(db, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Sensor con id {sensor_id} no encontrado")
    mags = crud_sm.get_by_sensor(db, sensor_id)
    return [
        {
            "id": m.id,
            "sensor_id": m.sensor_id,
            "magnitud": m.magnitud,
            "unidad": m.unidad,
            "valor_minimo": float(m.valor_minimo),
            "valor_maximo": float(m.valor_maximo),
        }
        for m in mags
    ]


@router.get("/{sensor_id}/mediciones", summary="Historico de mediciones con filtros")
def historico(
    sensor_id: int,
    magnitud: Optional[str] = Query(default=None, description="Filtrar por magnitud, ej. temperature"),
    desde: Optional[str] = Query(default=None, description="ISO-8601 inicio, ej. 2026-10-08T00:00:00Z"),
    hasta: Optional[str] = Query(default=None, description="ISO-8601 fin"),
    limit: Optional[int] = Query(default=None, gt=0, le=1000, description="Ultimas N mediciones"),
    db: Session = Depends(get_db),
):
    s = crud_sensor.get_by_id(db, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Sensor con id {sensor_id} no encontrado")

    try:
        desde_dt = parse_filtro_fecha(desde) if desde else None
        hasta_dt = parse_filtro_fecha(hasta) if hasta else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if desde_dt and hasta_dt and desde_dt > hasta_dt:
        raise HTTPException(
            status_code=400,
            detail="Rango invalido: 'desde' es posterior a 'hasta'",
        )

    if magnitud:
        cfg = crud_sm.get_by_sensor_and_magnitud(db, sensor_id, magnitud)
        if not cfg:
            raise HTTPException(
                status_code=404,
                detail=f"Magnitud '{magnitud}' no configurada para el sensor {sensor_id}",
            )

    rows = crud_medicion.list_by_sensor(
        db, sensor_id, magnitud=magnitud, desde=desde_dt, hasta=hasta_dt, limit=limit
    )
    # Completar sensor_codigo cuando la relacion no lo trae
    out = []
    for m in rows:
        d = _medicion_out(m)
        if not d["sensor_codigo"]:
            d["sensor_codigo"] = s.codigo
            d["sensor_id"] = s.id
        out.append(d)
    return out


@router.get("/{sensor_id}/ultima-medicion", summary="Ultima medicion (todas las magnitudes del ultimo timestamp)")
def ultima_medicion(sensor_id: int, db: Session = Depends(get_db)):
    s = crud_sensor.get_by_id(db, sensor_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Sensor con id {sensor_id} no encontrado")
    rows = crud_medicion.get_last_by_sensor(db, sensor_id)
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"El sensor {sensor_id} aun no tiene mediciones almacenadas",
        )
    out = []
    for m in rows:
        d = _medicion_out(m)
        if not d["sensor_codigo"]:
            d["sensor_codigo"] = s.codigo
            d["sensor_id"] = s.id
        out.append(d)
    return out
