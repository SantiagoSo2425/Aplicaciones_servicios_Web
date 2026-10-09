# Resultados automaticos

Fecha: 2026-10-08T21:01:36.768753+00:00
Sensor asignado: ENV-001 (id 14)
Sensor p/historico: GAS-002 (id 5)

| # | Prueba | Tipo | Esperado | Obtenido | OK |
|---|---|---|---|---|---|
| 8 | Consulta por ID existente | HTTP | 200 | 200 | SI |
| 9 | Consulta por ID inexistente | HTTP | 404 | 404 | SI |
| 10 | Consulta historica | HTTP | 200 | 200 | SI |
| 11 | Consulta por rango de fechas | HTTP | 200 | 200 | SI |
| 12 | Rango desde>hasta -> 400 | HTTP | 400 | 400 | SI |
| 13 | Validacion HTTP incorrecta -> 422 | HTTP | 422 | 422 | SI |
| 13 | Validacion path incorrecta -> 422 (b) | HTTP | 422 | 422 | SI |
| 14 | Ultima medicion | HTTP | 200 | 200 | SI |
| 15 | Ultimas N mediciones (limit) | HTTP | 200 | 200 | SI |
| 16 | Filtro por magnitud | HTTP | 200 | 200 | SI |
| 8 | Detalle sensor-magnitud existente (b) | HTTP | 200 | 200 | SI |
| 9 | Detalle sensor-magnitud inexistente -> 404 (b) | HTTP | 404 | 404 | SI |
| 2 | Medicion valida | MQTT | almacena=True | almaceno=True | SI |
| 3 | Sensor inexistente | MQTT | almacena=False | almaceno=False | SI |
| 4 | Unidad incorrecta | MQTT | almacena=False | almaceno=False | SI |
| 5 | Tipo de dato incorrecto (string) | MQTT | almacena=False | almaceno=False | SI |
| 6 | Magnitud incorrecta | MQTT | almacena=False | almaceno=False | SI |
| 7 | Timestamp invalido | MQTT | almacena=False | almaceno=False | SI |