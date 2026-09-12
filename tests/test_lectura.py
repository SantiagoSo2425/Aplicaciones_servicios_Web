import json

import pytest

from lectura import leer_proveedor_a, leer_proveedor_b


def test_leer_proveedor_a_archivo_inexistente_lanza_excepcion(tmp_path):
    with pytest.raises(FileNotFoundError):
        leer_proveedor_a(tmp_path / "no_existe.json")


def test_leer_proveedor_a_lee_todos_los_registros(tmp_path):
    ruta = tmp_path / "proveedor_a.json"
    ruta.write_text(
        json.dumps({"records": [{"provider_record_id": "A-1"}, {"provider_record_id": "A-2"}]}),
        encoding="utf-8",
    )
    registros = leer_proveedor_a(ruta)
    assert len(registros) == 2
    assert registros[0].origen_dataset == "proveedor_a"


def test_leer_proveedor_b_detecta_fila_csv_defectuosa(tmp_path):
    ruta = tmp_path / "proveedor_b.csv"
    encabezado = "record_code;municipality;country;latitude_deg;longitude_deg;temp_celsius;humidity_pct;wind_kmh;measurement_time;origin_code"
    fila_ok = "B-0001;Medellin;CO;6.26152;-75.575842;21.55;50.7;21.85;01/09/2026 06:00;PB"
    fila_defectuosa = "B-0002;Medellin;CO;6.26152;-75.575842;21.55;50.7;21.85"  # faltan columnas
    ruta.write_text(f"{encabezado}\n{fila_ok}\n{fila_defectuosa}\n", encoding="utf-8")

    registros, defectuosas = leer_proveedor_b(ruta)

    assert len(registros) == 1
    assert len(defectuosas) == 1
    assert defectuosas[0]["id_trazabilidad"] == "B-0002"
