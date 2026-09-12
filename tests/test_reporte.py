from reporte import construir_reporte


def test_construir_reporte_cuenta_cada_etapa_correctamente():
    seguimiento = [
        {"id_trazabilidad": "A-1", "origen_dataset": "proveedor_a", "etapa": "error_normalizacion", "detalle": "x"},
        {"id_trazabilidad": "A-2", "origen_dataset": "proveedor_a", "etapa": "rechazado_localmente", "detalle": []},
        {"id_trazabilidad": "A-3", "origen_dataset": "proveedor_a", "etapa": "aceptado_api", "detalle": {}},
        {"id_trazabilidad": "B-1", "origen_dataset": "proveedor_b", "etapa": "rechazado_api", "detalle": {}},
        {"id_trazabilidad": "B-2", "origen_dataset": "proveedor_b", "etapa": "error_comunicacion", "detalle": {}},
    ]

    reporte = construir_reporte(seguimiento, {"estado": "aceptado"})
    resumen = reporte["resumen"]

    assert resumen["procesados"] == 5
    assert resumen["errores_normalizacion"] == 1
    assert resumen["normalizados"] == 4
    assert resumen["rechazados_localmente"] == 1
    assert resumen["validos_localmente"] == 3
    assert resumen["enviados"] == 3
    assert resumen["aceptados_api"] == 1
    assert resumen["rechazados_api"] == 1
    assert resumen["errores_comunicacion"] == 1
