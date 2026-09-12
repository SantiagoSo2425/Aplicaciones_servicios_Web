from validacion import validar_registro


def _medicion_base(**overrides):
    base = {
        "ciudad": "Medellin",
        "pais": "CO",
        "latitud": 6.24,
        "longitud": -75.59,
        "temperatura_c": 18.9,
        "humedad": 81.3,
        "viento_kmh": 30.5,
        "fecha_hora": "2026-09-01T00:00:00-05:00",
        "origen": "proveedor_a",
    }
    base.update(overrides)
    return base


def test_registro_valido_no_tiene_errores():
    errores = validar_registro(_medicion_base())
    assert errores == []


def test_registro_con_humedad_fuera_de_rango_es_invalido():
    errores = validar_registro(_medicion_base(humedad=108.4))
    assert any("humedad" in e for e in errores)


def test_registro_con_ciudad_vacia_es_invalido():
    errores = validar_registro(_medicion_base(ciudad=""))
    assert any("ciudad" in e for e in errores)


def test_registro_con_viento_negativo_es_invalido():
    errores = validar_registro(_medicion_base(viento_kmh=-2.4))
    assert any("viento_kmh" in e for e in errores)
