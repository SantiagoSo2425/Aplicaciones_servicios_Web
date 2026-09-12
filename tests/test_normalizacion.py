import pytest

from lectura import RegistroCrudo
from normalizacion import (
    ErrorNormalizacion,
    normalizar_registro_a,
    normalizar_registro_b,
    _fahrenheit_a_celsius,
    _ms_a_kmh,
)


def test_conversion_fahrenheit_a_celsius():
    # 32F == 0C, 212F == 100C
    assert _fahrenheit_a_celsius(32) == pytest.approx(0.0)
    assert _fahrenheit_a_celsius(212) == pytest.approx(100.0)


def test_conversion_viento_ms_a_kmh():
    assert _ms_a_kmh(10) == pytest.approx(36.0)


def test_normalizar_registro_a_correcto():
    crudo = RegistroCrudo(
        "A-0001",
        "proveedor_a",
        {
            "station": {"city_name": "Medellin", "country_code": "CO"},
            "location": {"lat": 6.24, "lon": -75.59},
            "measurements": {
                "temperature_f": 66.1,
                "relative_humidity": 81.3,
                "wind_speed_ms": 8.47,
            },
            "observed_at": "2026-09-01T00:00:00-05:00",
        },
    )
    medicion = normalizar_registro_a(crudo)
    assert medicion["ciudad"] == "Medellin"
    assert medicion["pais"] == "CO"
    assert medicion["origen"] == "proveedor_a"
    assert medicion["temperatura_c"] == pytest.approx((66.1 - 32) * 5 / 9)
    assert medicion["viento_kmh"] == pytest.approx(8.47 * 3.6)


def test_normalizar_registro_a_temperatura_no_numerica_es_error():
    crudo = RegistroCrudo(
        "A-0082",
        "proveedor_a",
        {
            "station": {"city_name": "Medellin", "country_code": "CO"},
            "location": {"lat": 6.24, "lon": -75.59},
            "measurements": {
                "temperature_f": "N/A",
                "relative_humidity": 81.3,
                "wind_speed_ms": 8.47,
            },
            "observed_at": "2026-09-01T00:00:00-05:00",
        },
    )
    with pytest.raises(ErrorNormalizacion):
        normalizar_registro_a(crudo)


def test_normalizar_registro_b_fecha_sin_zona_horaria():
    crudo = RegistroCrudo(
        "B-0001",
        "proveedor_b",
        {
            "municipality": "Medellin",
            "country": "CO",
            "latitude_deg": "6.26152",
            "longitude_deg": "-75.575842",
            "temp_celsius": "21.55",
            "humidity_pct": "50.7",
            "wind_kmh": "21.85",
            "measurement_time": "01/09/2026 06:00",
        },
    )
    medicion = normalizar_registro_b(crudo)
    assert medicion["fecha_hora"].startswith("2026-09-01T06:00:00")
    assert medicion["origen"] == "proveedor_b"


def test_normalizar_registro_b_fecha_ausente_es_error():
    crudo = RegistroCrudo(
        "B-0076",
        "proveedor_b",
        {
            "municipality": "Medellin",
            "country": "CO",
            "latitude_deg": "6.26152",
            "longitude_deg": "-75.575842",
            "temp_celsius": "21.55",
            "humidity_pct": "50.7",
            "wind_kmh": "21.85",
            "measurement_time": "",
        },
    )
    with pytest.raises(ErrorNormalizacion):
        normalizar_registro_b(crudo)
