import requests

from cliente_api import ClienteApiInstitucional


class RespuestaFalsa:
    def __init__(self, status_code, cuerpo=None):
        self.status_code = status_code
        self._cuerpo = cuerpo if cuerpo is not None else {}

    def json(self):
        return self._cuerpo


class SesionFalsa:
    """Simula requests.Session sin hacer llamadas de red reales."""

    def __init__(self, respuestas=None, excepciones=None):
        self.respuestas = list(respuestas or [])
        self.excepciones = list(excepciones or [])
        self.llamadas = 0

    def post(self, url, json=None, headers=None, timeout=None):
        self.llamadas += 1
        if self.excepciones:
            exc = self.excepciones.pop(0)
            if exc is not None:
                raise exc
        return self.respuestas.pop(0)

    def get(self, url, params=None, timeout=None):
        self.llamadas += 1
        return self.respuestas.pop(0)


def test_envio_exitoso_no_reintenta():
    sesion = SesionFalsa(respuestas=[RespuestaFalsa(201, {"id": "srv-1"})])
    cliente = ClienteApiInstitucional("http://api.test", "equipo1", sesion=sesion)

    resultado = cliente.enviar_medicion({"ciudad": "Medellin"})

    assert resultado.estado == "aceptado"
    assert resultado.intentos == 1
    assert sesion.llamadas == 1


def test_error_4xx_no_se_reintenta():
    sesion = SesionFalsa(respuestas=[RespuestaFalsa(422, {"error": "dato inválido"})])
    cliente = ClienteApiInstitucional("http://api.test", "equipo1", sesion=sesion)

    resultado = cliente.enviar_medicion({"ciudad": "Medellin"})

    assert resultado.estado == "rechazado"
    assert resultado.intentos == 1
    assert sesion.llamadas == 1


def test_error_5xx_se_reintenta_hasta_exito():
    sesion = SesionFalsa(
        respuestas=[RespuestaFalsa(503), RespuestaFalsa(500), RespuestaFalsa(201, {"id": "srv-2"})]
    )
    cliente = ClienteApiInstitucional("http://api.test", "equipo1", sesion=sesion)

    resultado = cliente.enviar_medicion({"ciudad": "Medellin"})

    assert resultado.estado == "aceptado"
    assert resultado.intentos == 3
    assert sesion.llamadas == 3


def test_error_5xx_persistente_agota_reintentos_como_error_comunicacion():
    sesion = SesionFalsa(
        respuestas=[RespuestaFalsa(503), RespuestaFalsa(503), RespuestaFalsa(503)]
    )
    cliente = ClienteApiInstitucional("http://api.test", "equipo1", sesion=sesion)

    resultado = cliente.enviar_medicion({"ciudad": "Medellin"})

    assert resultado.estado == "error_comunicacion"
    assert resultado.intentos == 3
    assert sesion.llamadas == 3


def test_timeout_cuenta_como_error_comunicacion_tras_agotar_intentos():
    sesion = SesionFalsa(
        excepciones=[requests.Timeout(), requests.Timeout(), requests.Timeout()],
        respuestas=[],
    )
    cliente = ClienteApiInstitucional("http://api.test", "equipo1", sesion=sesion)

    resultado = cliente.enviar_medicion({"ciudad": "Medellin"})

    assert resultado.estado == "error_comunicacion"
    assert resultado.intentos == 3
