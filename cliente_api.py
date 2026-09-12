"""Cliente HTTP para la API institucional descrita en CONTRATO_API.md.

Implementa el envío de mediciones (POST /api/v1/mediciones) con la política
de reintentos exigida (1 intento inicial + hasta 2 reintentos, solo ante
5xx/timeout/pérdida de conexión) y la consulta de resultados
(GET /api/v1/mediciones).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

MAX_INTENTOS = 3


@dataclass
class ResultadoEnvio:
    estado: str  # "aceptado" | "rechazado" | "error_comunicacion"
    intentos: int
    http_status: int | None = None
    cuerpo_respuesta: Any = None
    detalle: str | None = None


class ClienteApiInstitucional:
    def __init__(self, url_base: str, equipo: str, timeout: float = 10.0, sesion: requests.Session | None = None):
        self.url_base = url_base.rstrip("/")
        self.equipo = equipo
        self.timeout = timeout
        self.sesion = sesion or requests.Session()

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json", "X-Equipo": self.equipo}

    def _parsear_cuerpo(self, respuesta: requests.Response) -> Any:
        try:
            return respuesta.json()
        except ValueError:
            return None

    def enviar_medicion(self, medicion: dict[str, Any]) -> ResultadoEnvio:
        """Envía una medición, reintentando solo ante errores transitorios."""
        url = f"{self.url_base}/api/v1/mediciones"
        ultimo_error = None

        for intento in range(1, MAX_INTENTOS + 1):
            try:
                respuesta = self.sesion.post(
                    url, json=medicion, headers=self._headers(), timeout=self.timeout
                )
            except (requests.Timeout, requests.ConnectionError) as exc:
                ultimo_error = str(exc)
                if intento < MAX_INTENTOS:
                    continue
                return ResultadoEnvio(
                    estado="error_comunicacion", intentos=intento, detalle=ultimo_error
                )
            except requests.RequestException as exc:
                return ResultadoEnvio(
                    estado="error_comunicacion", intentos=intento, detalle=str(exc)
                )

            cuerpo = self._parsear_cuerpo(respuesta)

            if respuesta.status_code == 201:
                return ResultadoEnvio(
                    estado="aceptado",
                    intentos=intento,
                    http_status=respuesta.status_code,
                    cuerpo_respuesta=cuerpo,
                )

            if 400 <= respuesta.status_code < 500:
                return ResultadoEnvio(
                    estado="rechazado",
                    intentos=intento,
                    http_status=respuesta.status_code,
                    cuerpo_respuesta=cuerpo,
                )

            if respuesta.status_code >= 500:
                ultimo_error = f"HTTP {respuesta.status_code}"
                if intento < MAX_INTENTOS:
                    continue
                return ResultadoEnvio(
                    estado="error_comunicacion",
                    intentos=intento,
                    http_status=respuesta.status_code,
                    cuerpo_respuesta=cuerpo,
                    detalle=ultimo_error,
                )

            return ResultadoEnvio(
                estado="rechazado",
                intentos=intento,
                http_status=respuesta.status_code,
                cuerpo_respuesta=cuerpo,
                detalle="código HTTP no contemplado en el contrato",
            )

        return ResultadoEnvio(estado="error_comunicacion", intentos=MAX_INTENTOS, detalle=ultimo_error)

    def consultar_mediciones(self) -> ResultadoEnvio:
        """Consulta las mediciones registradas para el equipo (sin reintentos)."""
        url = f"{self.url_base}/api/v1/mediciones"
        try:
            respuesta = self.sesion.get(
                url, params={"equipo": self.equipo}, timeout=self.timeout
            )
        except requests.RequestException as exc:
            return ResultadoEnvio(estado="error_comunicacion", intentos=1, detalle=str(exc))

        cuerpo = self._parsear_cuerpo(respuesta)
        if respuesta.status_code == 200:
            return ResultadoEnvio(
                estado="aceptado", intentos=1, http_status=200, cuerpo_respuesta=cuerpo
            )
        return ResultadoEnvio(
            estado="rechazado",
            intentos=1,
            http_status=respuesta.status_code,
            cuerpo_respuesta=cuerpo,
        )
