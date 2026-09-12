# Análisis — Taller 1: Integración de datos entre aplicaciones

**Equipo:** EQUIPO-10-APPSWEB
**Integrantes:** Juan Carlos Monsalve, Santiago Suárez Osorio

## 1. Diferencias entre los contratos de los proveedores

| Aspecto | Proveedor A (JSON) | Proveedor B (CSV) | Contrato institucional |
|---|---|---|---|
| Ciudad | `station.city_name` | `municipality` | `ciudad` (string, no vacío) |
| País | `station.country_code` (a veces ausente) | `country` | `pais` (string, no vacío) |
| Latitud/Longitud | `location.lat` / `location.lon` (float) | `latitude_deg` / `longitude_deg` (string numérica) | `latitud` -90..90, `longitud` -180..180 |
| Temperatura | `measurements.temperature_f` en **Fahrenheit** | `temp_celsius` en **Celsius**, como string | `temperatura_c` numérico en Celsius |
| Humedad | `measurements.relative_humidity` (0-100 esperado) | `humidity_pct` (string) | `humedad` 0..100 |
| Viento | `measurements.wind_speed_ms` en **m/s** | `wind_kmh` en **km/h**, como string | `viento_kmh` >= 0 |
| Fecha/hora | `observed_at`, ISO 8601 con offset (`-05:00`) | `measurement_time`, formato `DD/MM/YYYY HH:MM` **sin zona horaria** | `fecha_hora` ISO 8601 |
| Origen | campo `source` (`weather_provider_a`, no reutilizable directamente) | `origin_code` (`PB`, tampoco coincide con el valor institucional) | `origen` ∈ {`proveedor_a`, `proveedor_b`} |
| Identificador | `provider_record_id` (p. ej. `A-0001`) | `record_code` (p. ej. `B-0001`) | no forma parte del body; se usa solo como trazabilidad interna |
| Estructura | JSON anidado (`station`, `location`, `measurements`) | tabla plana delimitada por `;` | objeto plano |

El proveedor A anida la información en sub-objetos y usa unidades imperiales (°F, m/s); el proveedor B es una tabla plana delimitada por `;` (no por `,`), con todos los valores numéricos representados como texto y sin zona horaria en las fechas.

## 2. Transformaciones necesarias

- **Temperatura**: conversión Fahrenheit → Celsius para el proveedor A (`(°F − 32) × 5/9`); el proveedor B ya viene en Celsius pero como texto, por lo que solo requiere `float()`.
- **Viento**: conversión m/s → km/h para el proveedor A (`× 3.6`); el proveedor B ya viene en km/h.
- **Fecha/hora**: el proveedor A ya trae ISO 8601 con offset, solo se reformatea; el proveedor B trae `DD/MM/YYYY HH:MM` sin huso horario — se decidió asumir el mismo huso que usa el proveedor A en sus datos (UTC-05:00, hora de Colombia), documentado como supuesto explícito en `normalizacion.py`.
- **Origen**: no se copia del dataset (`source`/`origin_code`), se asigna de forma fija (`proveedor_a` / `proveedor_b`) según el archivo de procedencia, porque son los únicos valores permitidos por el contrato.
- **Tipos**: todos los campos numéricos de texto del proveedor B se convierten explícitamente a `float`.
- **Identificador de trazabilidad**: se conserva el id original del proveedor (`provider_record_id` / `record_code`) fuera del body enviado a la API, únicamente para el reporte y `normalizadas.json`.

## 3. Tipos de errores encontrados antes de enviar información

**Errores de normalización** (el dato no puede convertirse al tipo exigido; el registro no se envía ni se incluye en `normalizadas.json`):

- Temperatura no numérica o ausente (`"N/A"`, `null`, cadena vacía).
- Fecha/hora ausente o con formato inválido (por ejemplo `"31/13/2026 28:75"`, una fecha inexistente).

**Rechazos de validación local** (el dato se normaliza correctamente pero incumple una regla del contrato; el registro sí queda en `normalizadas.json` pero no se envía):

- Humedad fuera de 0–100 %.
- Latitud fuera de -90..90 o longitud fuera de -180..180.
- Viento negativo.
- Ciudad o país vacíos.

En la ejecución real sobre los 400 registros suministrados (200 por proveedor) se identificaron 8 errores de normalización y 12 rechazos de validación local (ver evidencia en la sección 6).

## 4. Diferencias entre validación local y validación del servidor

La validación local solo puede verificar lo que el contrato documenta explícitamente (rangos numéricos, campos no vacíos, tipos). El servidor, en cambio, puede aplicar reglas adicionales no documentadas —por ejemplo, duplicados (`409 Conflicto`) o reglas de negocio internas que producen `422` incluso sobre registros que localmente parecían correctos—. Por eso el cliente nunca asume que "válido localmente" equivale a "aceptado por la API": siempre interpreta la respuesta real del servidor y la registra en el reporte, tal como exige el contrato.

## 5. Decisión de implementación más importante

La decisión más importante fue separar con claridad **normalización** (¿puedo representar este dato en el tipo del contrato?) de **validación** (¿este dato, ya bien tipado, cumple las reglas de negocio?). Esta distinción determina en qué archivo termina cada registro (`normalizadas.json` sí/no) y evita mezclar dos causas de rechazo muy distintas bajo un mismo error genérico, lo que a su vez hace que el reporte final sea realmente útil para diagnosticar dónde falla la integración (fuente de datos vs. reglas de negocio vs. servidor).

## 6. Evidencia de una ejecución real

Ejecución: `python integrador.py` contra `https://appsweb.quantaiot.co`, equipo `EQUIPO-10-APPSWEB`.

Resumen (`salida/reporte.json` → `resumen`):

```
procesados: 400
normalizados: 392
errores_normalizacion: 8
validos_localmente: 380
rechazados_localmente: 12
enviados: 380
aceptados_api: 380
rechazados_api: 0
errores_comunicacion: 0
```

Casos de error de normalización (8 en total, ejemplos): `A-0082` — temperatura `"N/A"` no interpretable como número; `A-0040` — sin campo `observed_at`; `B-0171` — fecha `"31/13/2026 28:75"` inválida.

Casos de rechazo local (12 en total, ejemplos): `A-0015` — humedad `108.4`, fuera del rango 0–100; `A-0031` — latitud `95.245`, fuera de -90..90; `A-0088` — viento `-8.64` km/h, negativo; `A-0136` — ciudad vacía.

Respuesta de la API a un envío exitoso (`id_trazabilidad = A-0001`):

```json
{
  "http_status": 201,
  "intentos": 1,
  "cuerpo_respuesta": {
    "id": 1531,
    "estado": "aceptada",
    "mensaje": "Medición registrada correctamente"
  }
}
```

Resultado de la consulta final (`GET /api/v1/mediciones?equipo=EQUIPO-10-APPSWEB`):

```json
{
  "http_status": 200,
  "estado": "aceptado",
  "cuerpo_respuesta": {
    "equipo": "EQUIPO-10-APPSWEB",
    "total": 381,
    "mediciones": ["... 381 mediciones registradas, incluye las 380 de esta ejecución más 1 de prueba previa ..."]
  }
}
```

Los 380 registros enviados fueron aceptados por la API (0 rechazados por el servidor, 0 errores de comunicación), y la consulta final confirma que quedaron almacenados bajo el equipo `EQUIPO-10-APPSWEB`.
