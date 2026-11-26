"""Entidades base y clase Cliente con encapsulación y validaciones estrictas."""

from abc import ABC, abstractmethod
from datetime import datetime
import re

from excepciones import ErrorValidacionCliente


class EntidadBase(ABC):
    """Clase abstracta que representa entidades generales del sistema."""

    def __init__(self, id_entidad: str):
        self._id = self._validar_id(id_entidad)
        self._fecha_creacion = datetime.now()

    @staticmethod
    def _validar_id(valor: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorValidacionCliente(
                "El identificador de la entidad debe ser un texto no vacío.",
                detalles={"id_recibido": valor},
            )
        return valor.strip().upper()

    @property
    def id(self) -> str:
        """Retorna el identificador único de la entidad."""
        return self._id

    @property
    def fecha_creacion(self) -> datetime:
        """Retorna la fecha y hora de creación de la entidad."""
        return self._fecha_creacion

    @abstractmethod
    def resumen(self) -> str:
        """Retorna una descripción resumida de la entidad."""

    @abstractmethod
    def validar_estado(self) -> bool:
        """Verifica que la entidad tenga un estado válido para operar."""


class Cliente(EntidadBase):
    """Representa un cliente de Software FJ con datos encapsulados y validados."""

    _REGEX_EMAIL = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")

    def __init__(self, id_cliente: str, nombre: str, correo: str, telefono: str, es_corporativo: bool = False):
        super().__init__(id_cliente)
        self._nombre = self._validar_nombre(nombre)
        self._correo = self._validar_correo(correo)
        self._telefono = self._validar_telefono(telefono)
        self._es_corporativo = bool(es_corporativo)

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ErrorValidacionCliente(
                "El nombre del cliente debe tener al menos 3 caracteres.",
                detalles={"nombre": nombre},
            )
        return nombre.strip().title()

    @classmethod
    def _validar_correo(cls, correo: str) -> str:
        if not isinstance(correo, str) or not cls._REGEX_EMAIL.match(correo.strip()):
            raise ErrorValidacionCliente(
                "El correo electrónico del cliente no tiene un formato válido.",
                detalles={"correo": correo},
            )
        return correo.strip().lower()

    @staticmethod
    def _validar_telefono(telefono: str) -> str:
        limpio = "".join(ch for ch in str(telefono) if ch.isdigit())
        if len(limpio) < 7 or len(limpio) > 15:
            raise ErrorValidacionCliente(
                "El teléfono del cliente debe contener entre 7 y 15 dígitos.",
                detalles={"telefono": telefono},
            )
        return limpio

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre: str) -> None:
        self._nombre = self._validar_nombre(nuevo_nombre)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, nuevo_correo: str) -> None:
        self._correo = self._validar_correo(nuevo_correo)

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, nuevo_telefono: str) -> None:
        self._telefono = self._validar_telefono(nuevo_telefono)

    @property
    def es_corporativo(self) -> bool:
        return self._es_corporativo

    def resumen(self) -> str:
        tipo = "Corporativo" if self._es_corporativo else "Particular"
        return f"[{self._id}] {self._nombre} ({tipo}) - {self._correo} | Tel: {self._telefono}"

    def validar_estado(self) -> bool:
        return bool(self._id and self._nombre and self._correo and self._telefono)

    def __str__(self) -> str:
        return self.resumen()