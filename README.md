# Taller 2 — API para adquisición y consulta de datos IoT

**Asignatura:** Aplicaciones y Servicios Web — Tecnología en Desarrollo de Software
**Fecha:** Octubre 2026
**Integrantes:** Santiago Suarez Osorio y Juan Carlos Monsalve Restrepo
**Sensor asignado:** `ENV-001` (asignado por el docente)
**Tópico configurado (`.env`):** `iot/sensors/ENV-001/data`
**Broker:** `emqx.coriotlab.co:1883` — **PostgreSQL:** `190.248.28.132:3002/appdb`

> Estado actual: proyecto funcional con sensor ENV-001 confirmado. En colecta de 20 min para completar el histórico propio.

## 1. Información general

| Campo | Valor |
|---|---|
| Proyecto | taller-2-iot-api (FastAPI + MQTT + PostgreSQL) |
| Integrantes | 1) Santiago Suarez Osorio — 2) Juan Carlos Monsalve Restrepo |
| Asignatura | Aplicaciones y Servicios Web |
| Fecha | 08-10-2026 |
| Sensor asignado | ENV-001 (id 14) — Sensor ambiental general |
| Tópico MQTT | `iot/sensors/ENV-001/data` |

## 2. Descripción del sistema

**Problema:** infraestructura IoT con 15 sensores (aire, gases, agua, ambiente) que publican cada ~5 s en `iot/sensors/{codigo}/data`. Se debe suscribirse al tópico asignado, validar cada mensaje, guardar solo los válidos y exponer consultas HTTP.

**Arquitectura:**

```
Sensor --MQTT JSON--> [app/mqtt/client.py] --> [app/mqtt/processor.py]
    --> Pydantic (app/schemas/medicion.py:MqttPayload)
    --> ORM (app/crud/sensor.py, sensor_magnitud.py) + reglas negocio
    --> PostgreSQL (tabla mediciones, 1 fila por magnitud, mismo timestamp_utc)
Cliente HTTP --> FastAPI (app/main.py + app/api/*.py) --> ORM --> PostgreSQL
                      timestamps UTC en BD, respuestas en America/Bogota
```

**Magnitudes/unidades (catálogo real verificado 08-oct-2026):**

- `ENV-001` (provisional): `temperature/C [-10,60]`, `humidity/% [0,100]`, `pressure/hPa [800,1200]`
- `GAS-002` (con datos): `ch4/ppm [0,2000]`, `temperature/C [10,50]`, `humidity/% [0,100]`
- Ver las 40 magnitudes en `data-model.md` y `GET /sensores/{id}/magnitudes`.

**Payload real observado (broker):**

```json
{
  "sensor_id": "ENV-001",
  "timestamp": "2026-10-08T20:57:41Z",
  "measurements": {
    "temperature": {"value": 20.38, "unit": "C"},
    "humidity": {"value": 63.55, "unit": "%"},
    "pressure": {"value": 1078.27, "unit": "hPa"}
  }
}
```

Casos inválidos intencionales observados y rechazados: `illuminance.value` como string `"1795.39"`, `pm10` sin `unit`, magnitud extra `co2` en `AQ-003/GAS-005`, `humidity.unit=INVALID_UNIT`, `humidity` sin `value`, `temperature` sin `unit`.

## 3. Configuración del entorno

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # luego editar MQTT_TOPIC y credenciales DB
# Verificar BD:
python -c "from app.database.connection import engine; from sqlalchemy import text; print(engine.connect().execute(text('select count(*) from sensores')).scalar())"
# Correr API (con MQTT en background):
uvicorn app.main:app --reload --port 8000
# Solo consumidor MQTT (sin API):
python run_mqtt.py
# Colecta 20 min (cuando tengas sensor asignado):
python scripts/colectar_20min.py --minutos 20
# Evidencias automáticas:
python scripts/generar_evidencias.py
```

Docs: `http://localhost:8000/docs` — Salud: `GET /health`.

**Variables de entorno (sin valores sensibles):** `DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DATABASE_URL(opcional), MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD, MQTT_KEEPALIVE, ENABLE_MQTT`. Ver `.env.example`. `.env` está en `.gitignore` y no se sube.

## 4. Base de datos

- **Conexión:** `app/database/connection.py` — `engine` + `SessionLocal` + `Base` + dependencia `get_db()`. URL `postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME` desde `DATABASE_URL` o partes `DB_*`. `pool_pre_ping=True`.
- **Tablas (corresponden 1:1 con `data-model.md`):**
  - `sensores` → `app/models/sensor.py:Sensor` (PK `id`, UNIQUE `codigo`)
  - `sensor_magnitudes` → `app/models/sensor_magnitud.py:SensorMagnitud` (FK `sensor_id→sensores.id CASCADE/RESTRICT`, UNIQUE `(sensor_id,magnitud)`, CHECK `min<max`)
  - `mediciones` → `app/models/medicion.py:Medicion` (PK `BIGSERIAL id`, FK `sensor_magnitud_id→sensor_magnitudes.id CASCADE/RESTRICT`, `valor NUMERIC(12,4)`, `timestamp_utc TIMESTAMPTZ`, `fecha_recepcion TIMESTAMPTZ DEFAULT NOW()`)
- **Relaciones:** `Sensor 1:N SensorMagnitud 1:N Medicion`, ambas `ON DELETE RESTRICT` (protegen catálogo e histórico). Índices de `mediciones` ya existen en el servidor.
- **Catálogo:** 15 sensores, 40 magnitudes, solo lectura desde la app (no hay POST/PUT/DELETE de sensores/magnitudes).

## 5. Organización del código

```
app/
  main.py                  # FastAPI + lifespan MQTT + routers + /health
  database/connection.py   # engine, SessionLocal, Base, get_db()
  models/sensor.py, sensor_magnitud.py, medicion.py   # tablas ORM
  schemas/sensor.py, sensor_magnitud.py, medicion.py  # Pydantic Out + MqttPayload estricto
  crud/sensor.py, sensor_magnitud.py, medicion.py     # solo lecturas en catálogo; create_many+filtros en mediciones
  api/sensor.py, sensor_magnitud.py, medicion.py      # routers HTTP + errores 400/404/422 + conversión Bogota
  mqtt/client.py           # suscripción, on_connect/on_message, modo background y run_forever
  mqtt/processor.py        # process_payload(): Pydantic→ORM/negocio→insert o rechazo
  utils/timezone.py        # to_bogota_iso(), parse_filtro_fecha(), ensure_aware_utc()
```

| Capa | Función |
|---|---|
| `schemas/` | Contratos. `MqttPayload` valida estructura/campos/tipos estrictos (`StrictInt/StrictFloat` rechaza `"1795.39"`) y `timestamp` con zona. `*Out` definen respuestas. |
| `models/` | Tablas ORM + FK/UNIQUE/CHECK + `relationship`. |
| `crud/` | Acceso BD. Sensores/magnitudes solo `get_*`; mediciones `create_many`, `get_by_id`, `list_by_sensor(magnitud,desde,hasta,limit)`, `get_last_by_sensor`. |
| `api/` | HTTP. Serializa a Bogotá, valida `desde/hasta/limit/magnitud`, lanza 400/404/422. |
| `mqtt/` | Ingesta. `client.py` escucha; `processor.py:process_payload` decide almacenar (todas las magnitudes válidas → N filas mismo `timestamp_utc`) o rechazar (0 filas). |
| `database/` | Conexión y sesión por request. |

Validaciones: **Pydantic** = estructura, obligatorios, tipos, timestamp con zona. **ORM+negocio** (`processor.py`) = sensor existe/activo, magnitud configurada, unidad exacta, `min≤valor≤max`, FK consistentes. Timestamps se guardan UTC y se responden en `America/Bogota` ISO (`2026-10-08T15:57:41-05:00`) vía `utils/timezone.py:to_bogota_iso`.

## 6. Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` , `/health` | Estado API + BD |
| GET | `/sensores` | Listar 15 sensores |
| GET | `/sensores/{id}` | Sensor por PK numérica (404 si no existe, 422 si id no es int) |
| GET | `/sensores/por-codigo/{codigo}` | Sensor por `codigo` (= `sensor_id` MQTT) |
| GET | `/sensores/{id}/magnitudes` | Magnitudes configuradas (FK sensor→magnitudes) |
| GET | `/sensor-magnitudes/{id}` | Detalle de una magnitud (404 si no existe) |
| GET | `/mediciones/{id}` | Medición por PK con magnitud/unidad/sensor + timestamps Bogotá |
| GET | `/sensores/{id}/mediciones?magnitud=&desde=&hasta=&limit=` | Histórico filtrable/combinable, orden desc, `limit` = últimas N |
| GET | `/sensores/{id}/ultima-medicion` | Todas las magnitudes del `timestamp_utc` más reciente (404 si sin datos) |

Filtros: `magnitud` (404 si no configurada), `desde/hasta` ISO-8601 (400 si formato malo o `desde>hasta`), `limit` 1–1000 (422 si no es int).

## 7. Evidencias de funcionamiento

Carpeta `evidencias/` + generador `scripts/generar_evidencias.py` (18 casos OK el 08-oct-2026, ver `resultados.json` y `RESUMEN.md`). Colecta real: `scripts/colectar_20min.py --minutos 20` → `evidencias/colecta_20min.log` *(pendiente con sensor asignado)*.

| # | Prueba | Entrada | Resultado | Código | Archivo:función |
|---|---|---|---|---|---|
| 1 | Recepción MQTT | suscripción a `iot/sensors/ENV-001/data` | mensajes JSON cada ~5 s (ver log) | — | `app/mqtt/client.py:_on_message` |
| 2 | Medición válida | payload ENV-001 3 magnitudes válidas | 3 filas mismo `timestamp_utc` | — (interno OK) | `app/mqtt/processor.py:process_payload` + `app/crud/medicion.py:create_many` |
| 3 | Sensor inexistente | `sensor_id=FAKE-999` | rechazado, 0 filas | — | `processor.py:process_payload` (get_by_codigo) |
| 4 | Unidad incorrecta | `humidity/INVALID_UNIT` | rechazado | — | `processor.py` (compara `cfg.unidad`) |
| 5 | Tipo incorrecto | `value="1795.39"` string | rechazado Pydantic strict | — | `app/schemas/medicion.py:MqttPayload/MeasurementItem` |
| 6 | Magnitud incorrecta | `co2` en ENV-002 | rechazado | — | `processor.py` (get_by_sensor_and_magnitud None) |
| 7 | Timestamp inválido | `no-es-fecha` / sin zona | rechazado Pydantic | — | `schemas/medicion.py:timestamp_formato` |
| 8 | Por ID existente | `GET /sensores/14`, `/sensor-magnitudes/1` | JSON sensor/magnitud | 200 | `app/api/sensor.py:por_id`, `sensor_magnitud.py:por_id` |
| 9 | Por ID inexistente | `GET /sensores/999999` | `{"detail":...}` | 404 | mismos |
| 10 | Histórica | `GET /sensores/5/mediciones?limit=10` | lista (GAS-002) | 200 | `api/sensor.py:historico` + `crud/medicion.py:list_by_sensor` |
| 11 | Rango fechas | `?desde=2026-10-01T00:00:00Z&hasta=2026-10-09T00:00:00Z` | filtrado | 200 | `utils/timezone.py:parse_filtro_fecha` |
| 12 | `desde>hasta` | `desde=09&hasta=08` | `Rango invalido` | 400 | `api/sensor.py:historico` |
| 13 | Validación HTTP | `?limit=abc`, `/sensores/abc` | detalle FastAPI | 422 | FastAPI+Pydantic (query/path) |
| 14 | Última medición | `GET /sensores/5/ultima-medicion` | filas del max timestamp | 200 (404 si sin datos) | `crud/medicion.py:get_last_by_sensor` |
| 15 | Últimas N | `?limit=3` | 3 filas desc | 200 | `list_by_sensor(limit)` |
| 16 | Filtro magnitud | `?magnitud=ch4` | solo ch4 | 200 (404 si no configurada) | mismo |
| 17 | FK | `/{id}/magnitudes`, `mediciones` con `sensor_magnitud_id`, joins | relaciones OK | 200 | `models/*.py` + `crud/medicion.py:_base_query_sensor` |
| 18 | Separación | `app/{main,database,models,schemas,crud,api,mqtt,utils}` cada tabla con su archivo | estructura verificable | — | árbol del repo |

Conversión horaria verificada: `2026-10-08T20:57:41Z` (UTC) → `2026-10-08T15:57:41-05:00` (Bogotá) en todos los GET.

## 8. Control de versiones

- Repositorio del equipo: *(pegar enlace aquí antes de entregar en Teams)*
- Rama: `taller-2` (crear desde `main`).
- Commits: cada integrante debe tener commits identificables con mensajes descriptivos (`git log --oneline --graph` como evidencia).
- Aportes:
  - Santiago Suarez Osorio: configuración entorno y BD, modelos ORM, MQTT + colecta 20 min ENV-001, evidencias 1–7.
  - Juan Carlos Monsalve Restrepo: endpoints FastAPI + filtros, conversión Bogotá, evidencias 8–16, README.
  - *(Base inicial generada con asistencia; colecta y pruebas ejecutadas por el equipo.)*

```bash
git checkout -b taller-2
git add .
git commit -m "feat: base FastAPI+MQTT+PostgreSQL taller 2"
git push -u origin taller-2
```

## 9. Conclusiones

- **Aprendizajes:** Pydantic estricto evita falsos válidos (strings numéricos); separar Pydantic (forma) de ORM+negocio (fondo) simplifica rechazos; guardar UTC y convertir solo en presentación evita errores de zona; `limit` + filtros combinables cubren histórico/última/N.
- **Dificultades:** broker publica inválidos intencionales (unidades, magnitudes extra, campos faltantes); BD compartida con datos de otros grupos; sensor asignado pendiente → histórico del asignado vacío (se usó GAS-002 con datos para demostrar filtros).
- **Soluciones:** `StrictInt/StrictFloat` + `extra=forbid`, rechazo total si una magnitud falla, mismo `timestamp_utc` por payload, validación `desde>hasta→400`, script de evidencias que limpia sus filas de prueba, colector de 20 min con log.

---

### Pendientes antes del 10-oct-2026 23:59

1. Pedir sensor por Teams (límite 9 oct), poner `MQTT_TOPIC=iot/sensors/{CODIGO}/data` en `.env`, actualizar este README (sensor, tópico, payload real, nombres y aportes).
2. `python scripts/colectar_20min.py --minutos 20` y guardar `evidencias/colecta_20min.log` + captura de `GET /sensores/{id}/ultima-medicion`.
3. `python scripts/generar_evidencias.py`, verificar 18 OK con el sensor asignado.
4. Crear repo del grupo, rama `taller-2`, commits de ambos, entregar enlace en Teams.
