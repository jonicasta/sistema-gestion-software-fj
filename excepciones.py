"""Excepciones personalizadas para el sistema integral de Software FJ."""


class ErrorSistemaFJ(Exception):
    """Excepción base del sistema Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL", detalles: dict | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.detalles = detalles or {}


class ErrorValidacionCliente(ErrorSistemaFJ):
    """Se lanza cuando los datos de un cliente no cumplen las reglas de validación."""

    def __init__(self, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje, codigo="ERR_CLIENTE", detalles=detalles)


class ErrorServicio(ErrorSistemaFJ):
    """Se lanza cuando hay parámetros inválidos o problemas en un servicio."""

    def __init__(self, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje, codigo="ERR_SERVICIO", detalles=detalles)


class ErrorCalculoCosto(ErrorSistemaFJ):
    """Se lanza cuando ocurre un cálculo inconsistente o valores inválidos en costos."""

    def __init__(self, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje, codigo="ERR_CALCULO", detalles=detalles)


class ErrorReserva(ErrorSistemaFJ):
    """Se lanza ante reservas inválidas, transiciones de estado prohibidas o falta de disponibilidad."""

    def __init__(self, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje, codigo="ERR_RESERVA", detalles=detalles)