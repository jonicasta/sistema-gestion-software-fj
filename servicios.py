"""Clase abstracta Servicio y servicios especializados con polimorfismo y sobrecarga."""

from abc import abstractmethod
from functools import singledispatchmethod

from entidades import EntidadBase
from excepciones import ErrorCalculoCosto, ErrorServicio


class Servicio(EntidadBase):
    """Clase abstracta base para los servicios ofrecidos por Software FJ."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True):
        super().__init__(id_servicio)
        self._nombre = self._validar_nombre_servicio(nombre)
        self._tarifa_base = self._validar_tarifa(tarifa_base)
        self._disponible = bool(disponible)

    @staticmethod
    def _validar_nombre_servicio(nombre: str) -> str:
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ErrorServicio(
                "El nombre del servicio debe tener al menos 3 caracteres.",
                detalles={"nombre_servicio": nombre},
            )
        return nombre.strip()

    @staticmethod
    def _validar_tarifa(tarifa: float) -> float:
        try:
            valor = float(tarifa)
        except (TypeError, ValueError) as exc:
            raise ErrorServicio(
                "La tarifa base debe ser un valor numérico válido.",
                detalles={"tarifa_recibida": tarifa},
            ) from exc

        if valor <= 0:
            raise ErrorServicio(
                "La tarifa base del servicio debe ser mayor que cero.",
                detalles={"tarifa_recibida": valor},
            )
        return valor

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, cantidad: float) -> None:
        """Valida los parámetros específicos del servicio para una cantidad/duración dada."""

    @abstractmethod
    def calcular_costo_base(self, cantidad: float) -> float:
        """Calcula el costo base del servicio según la cantidad o duración."""

    @abstractmethod
    def describir(self) -> str:
        """Retorna una descripción detallada del servicio."""

    def calcular_costo(
        self,
        cantidad: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ) -> float:
        """Método con sobrecarga por parámetros opcionales (descuento e impuesto)."""
        self.validar_parametros(cantidad)

        try:
            desc = float(descuento_pct)
            imp = float(impuesto_pct)
        except (TypeError, ValueError) as exc:
            raise ErrorCalculoCosto(
                "Los porcentajes de descuento e impuesto deben ser numéricos.",
                detalles={"descuento_pct": descuento_pct, "impuesto_pct": impuesto_pct},
            ) from exc

        if not (0.0 <= desc < 100.0):
            raise ErrorCalculoCosto(
                "El porcentaje de descuento debe estar entre 0 y menor que 100.",
                detalles={"descuento_pct": desc},
            )

        if imp < 0.0:
            raise ErrorCalculoCosto(
                "El porcentaje de impuesto no puede ser negativo.",
                detalles={"impuesto_pct": imp},
            )

        subtotal = self.calcular_costo_base(cantidad)
        if subtotal <= 0:
            raise ErrorCalculoCosto(
                "El cálculo del subtotal produjo un valor inconsistente (<= 0).",
                detalles={"subtotal": subtotal, "cantidad": cantidad},
            )

        con_descuento = subtotal * (1.0 - desc / 100.0)
        total = con_descuento * (1.0 + imp / 100.0)
        return round(total, 2)

    @singledispatchmethod
    def calcular_costo_sobrecargado(self, arg) -> float:
        """Sobrecarga polimórfica según tipo de argumento (int/float para cantidad o dict con opciones)."""
        raise ErrorCalculoCosto(
            f"Tipo de parámetro no soportado para calcular_costo_sobrecargado: {type(arg).__name__}",
            detalles={"tipo_recibido": type(arg).__name__},
        )

    @calcular_costo_sobrecargado.register
    def _(self, cantidad: int) -> float:
        return self.calcular_costo(float(cantidad))

    @calcular_costo_sobrecargado.register
    def _(self, cantidad: float) -> float:
        return self.calcular_costo(cantidad)

    @calcular_costo_sobrecargado.register
    def _(self, opciones: dict) -> float:
        if not isinstance(opciones, dict) or "cantidad" not in opciones:
            raise ErrorCalculoCosto(
                "El diccionario de opciones debe incluir la clave 'cantidad'.",
                detalles={"opciones": opciones},
            )
        return self.calcular_costo(
            cantidad=opciones["cantidad"],
            descuento_pct=opciones.get("descuento_pct", 0.0),
            impuesto_pct=opciones.get("impuesto_pct", 0.0),
        )

    def resumen(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return f"[{self._id}] {self._nombre} | Tarifa base: ${self._tarifa_base:,.2f} | {estado}"

    def validar_estado(self) -> bool:
        return bool(self._id and self._nombre and self._tarifa_base > 0)


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas (capacidad y duración en horas)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_hora: float, capacidad_personas: int, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not isinstance(capacidad_personas, int) or capacidad_personas <= 0:
            raise ErrorServicio(
                "La capacidad de la sala debe ser un entero positivo.",
                detalles={"capacidad_personas": capacidad_personas},
            )
        self._capacidad_personas = capacidad_personas

    @property
    def capacidad_personas(self) -> int:
        return self._capacidad_personas

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, (int, float)) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ErrorServicio(
                "La duración de reserva de sala (en horas) debe ser un número mayor que 0.",
                detalles={"horas": cantidad, "servicio": self._id},
            )
        if cantidad > 24:
            raise ErrorServicio(
                "Una reserva continua de sala no puede superar las 24 horas.",
                detalles={"horas": cantidad, "max_horas": 24},
            )

    def calcular_costo_base(self, cantidad: float) -> float:
        self.validar_parametros(cantidad)
        return float(cantidad) * self._tarifa_base

    def describir(self) -> str:
        return (
            f"Reserva de Sala '{self._nombre}' (Capacidad: {self._capacidad_personas} personas, "
            f"Tarifa: ${self._tarifa_base:,.2f}/h)"
        )


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos (unidades y duración en días)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_dia: float, unidades_disponibles: int, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_dia, disponible)
        if not isinstance(unidades_disponibles, int) or unidades_disponibles <= 0:
            raise ErrorServicio(
                "Las unidades disponibles de equipo deben ser un entero positivo.",
                detalles={"unidades_disponibles": unidades_disponibles},
            )
        self._unidades_disponibles = unidades_disponibles

    @property
    def unidades_disponibles(self) -> int:
        return self._unidades_disponibles

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, (int, float)) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ErrorServicio(
                "El tiempo de alquiler de equipo (en días) debe ser un número mayor que 0.",
                detalles={"dias": cantidad, "servicio": self._id},
            )
        if cantidad > 90:
            raise ErrorServicio(
                "El alquiler de equipo no puede exceder los 90 días consecutivos.",
                detalles={"dias": cantidad, "max_dias": 90},
            )

    def calcular_costo_base(self, cantidad: float) -> float:
        self.validar_parametros(cantidad)
        # Recargo ligero si el alquiler es de 1 solo día
        factor = 1.10 if cantidad == 1 else 1.0
        return float(cantidad) * self._tarifa_base * factor

    def describir(self) -> str:
        return (
            f"Alquiler de Equipo '{self._nombre}' (Stock: {self._unidades_disponibles} und., "
            f"Tarifa: ${self._tarifa_base:,.2f}/día)"
        )


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas/especializadas (duración en horas)."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_hora: float, area_especialidad: str, disponible: bool = True):
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not isinstance(area_especialidad, str) or not area_especialidad.strip():
            raise ErrorServicio(
                "El área de especialidad de la asesoría es obligatoria.",
                detalles={"area_especialidad": area_especialidad},
            )
        self._area_especialidad = area_especialidad.strip()

    @property
    def area_especialidad(self) -> str:
        return self._area_especialidad

    def validar_parametros(self, cantidad: float) -> None:
        if not isinstance(cantidad, (int, float)) or isinstance(cantidad, bool) or cantidad < 1:
            raise ErrorServicio(
                "Una asesoría especializada requiere al menos 1 hora de duración.",
                detalles={"horas": cantidad, "min_horas": 1},
            )
        if cantidad > 100:
            raise ErrorServicio(
                "La duración de asesoría por bloque no puede superar las 100 horas.",
                detalles={"horas": cantidad, "max_horas": 100},
            )

    def calcular_costo_base(self, cantidad: float) -> float:
        self.validar_parametros(cantidad)
        return float(cantidad) * self._tarifa_base

    def describir(self) -> str:
        return (
            f"Asesoría Especializada '{self._nombre}' [Área: {self._area_especialidad}] "
            f"(Tarifa: ${self._tarifa_base:,.2f}/h)"
        )