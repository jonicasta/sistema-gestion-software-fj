"""Gestión de reservas y orquestador del sistema en memoria con manejo avanzado de excepciones."""

from datetime import datetime
from enum import Enum

from entidades import Cliente, EntidadBase
from excepciones import (
    ErrorCalculoCosto,
    ErrorReserva,
    ErrorServicio,
    ErrorSistemaFJ,
    ErrorValidacionCliente,
)
from logger_config import configurar_logger
from servicios import Servicio


class EstadoReserva(str, Enum):
    """Estados posibles del ciclo de vida de una reserva."""

    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    COMPLETADA = "COMPLETADA"


class Reserva(EntidadBase):
    """Integra cliente, servicio, duración, costo y estado con control de transiciones."""

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ):
        super().__init__(id_reserva)

        if not isinstance(cliente, Cliente) or not cliente.validar_estado():
            raise ErrorReserva(
                "La reserva requiere una instancia válida de Cliente.",
                detalles={"id_reserva": id_reserva, "cliente": repr(cliente)},
            )

        if not isinstance(servicio, Servicio) or not servicio.validar_estado():
            raise ErrorReserva(
                "La reserva requiere una instancia válida de Servicio.",
                detalles={"id_reserva": id_reserva, "servicio": repr(servicio)},
            )

        if not servicio.disponible:
            raise ErrorReserva(
                f"El servicio '{servicio.nombre}' [{servicio.id}] no está disponible para nuevas reservas.",
                detalles={"id_reserva": id_reserva, "servicio_id": servicio.id},
            )

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = self._validar_duracion(duracion)
        self._estado = EstadoReserva.PENDIENTE
        self._fecha_actualizacion = datetime.now()
        self._costo_total = self._calcular_total(
            descuento_pct=descuento_pct,
            impuesto_pct=impuesto_pct,
        )

    @staticmethod
    def _validar_duracion(duracion: float) -> float:
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool) or duracion <= 0:
            raise ErrorReserva(
                "La duración de la reserva debe ser un número positivo mayor que cero.",
                detalles={"duracion": duracion},
            )
        return float(duracion)

    def _calcular_total(self, descuento_pct: float = 0.0, impuesto_pct: float = 0.0) -> float:
        try:
            return self._servicio.calcular_costo(
                cantidad=self._duracion,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
            )
        except (ErrorServicio, ErrorCalculoCosto) as exc:
            raise ErrorReserva(
                f"No fue posible calcular el costo de la reserva '{self._id}': {exc}",
                detalles={"id_reserva": self._id, "servicio_id": self._servicio.id},
            ) from exc

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> float:
        return self._duracion

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def confirmar(self) -> None:
        """Confirma la reserva si se encuentra en estado PENDIENTE."""
        if self._estado == EstadoReserva.CANCELADA:
            raise ErrorReserva(
                f"No se puede confirmar la reserva '{self._id}' porque ya fue cancelada.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )
        if self._estado == EstadoReserva.COMPLETADA:
            raise ErrorReserva(
                f"La reserva '{self._id}' ya fue completada.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )
        if self._estado == EstadoReserva.CONFIRMADA:
            raise ErrorReserva(
                f"La reserva '{self._id}' ya se encuentra confirmada.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )
        self._estado = EstadoReserva.CONFIRMADA
        self._fecha_actualizacion = datetime.now()

    def cancelar(self, motivo: str = "Cancelación solicitada") -> None:
        """Cancela la reserva si no ha sido completada previamente."""
        if self._estado == EstadoReserva.COMPLETADA:
            raise ErrorReserva(
                f"No se puede cancelar la reserva '{self._id}' porque ya está completada.",
                detalles={"id_reserva": self._id, "motivo": motivo},
            )
        if self._estado == EstadoReserva.CANCELADA:
            raise ErrorReserva(
                f"La reserva '{self._id}' ya estaba cancelada.",
                detalles={"id_reserva": self._id, "motivo": motivo},
            )
        self._estado = EstadoReserva.CANCELADA
        self._fecha_actualizacion = datetime.now()

    def procesar(self) -> str:
        """Procesa la reserva confirmada y la marca como COMPLETADA."""
        if self._estado == EstadoReserva.PENDIENTE:
            raise ErrorReserva(
                f"La reserva '{self._id}' debe confirmarse antes de procesarse.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )
        if self._estado == EstadoReserva.CANCELADA:
            raise ErrorReserva(
                f"No se puede procesar la reserva '{self._id}' porque está cancelada.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )
        if self._estado == EstadoReserva.COMPLETADA:
            raise ErrorReserva(
                f"La reserva '{self._id}' ya fue procesada anteriormente.",
                detalles={"id_reserva": self._id, "estado_actual": self._estado.value},
            )

        if self._costo_total <= 0:
            raise ErrorReserva(
                f"Costo inconsistente (${self._costo_total}) al procesar la reserva '{self._id}'.",
                detalles={"id_reserva": self._id, "costo_total": self._costo_total},
            )

        self._estado = EstadoReserva.COMPLETADA
        self._fecha_actualizacion = datetime.now()
        return (
            f"Reserva {self._id} procesada con éxito | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | Total: ${self._costo_total:,.2f}"
        )

    def resumen(self) -> str:
        return (
            f"[{self._id}] Estado: {self._estado.value} | Cliente: {self._cliente.nombre} "
            f"({self._cliente.id}) | Servicio: {self._servicio.nombre} | "
            f"Duración: {self._duracion} | Costo: ${self._costo_total:,.2f}"
        )

    def validar_estado(self) -> bool:
        return isinstance(self._estado, EstadoReserva) and self._costo_total > 0


class SistemaGestionFJ:
    """Gestor en memoria (listas y objetos) con manejo de excepciones y logs."""

    def __init__(self, archivo_log: str = "logs/sistema_fj.log"):
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []
        self.logger = configurar_logger(archivo_log=archivo_log)
        self._contador_operaciones = 0

    def registrar_cliente(self, cliente: Cliente) -> Cliente:
        self._contador_operaciones += 1
        try:
            if not isinstance(cliente, Cliente):
                raise ErrorValidacionCliente(
                    "El objeto proporcionado no corresponde a un Cliente válido.",
                    detalles={"tipo": type(cliente).__name__},
                )
            if any(c.id == cliente.id for c in self.clientes):
                raise ErrorValidacionCliente(
                    f"Ya existe un cliente registrado con el ID '{cliente.id}'.",
                    detalles={"id_cliente": cliente.id},
                )
            self.clientes.append(cliente)
        except ErrorSistemaFJ as exc:
            self.logger.error(
                "Op #%d | Fallo registro cliente: %s | %s",
                self._contador_operaciones,
                exc.mensaje,
                exc.detalles,
            )
            raise
        else:
            self.logger.info(
                "Op #%d | Cliente registrado: %s",
                self._contador_operaciones,
                cliente.resumen(),
            )
            return cliente
        finally:
            self.logger.info(
                "Op #%d | Finalizó intento de registro de cliente.",
                self._contador_operaciones,
            )

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        self._contador_operaciones += 1
        try:
            if not isinstance(servicio, Servicio):
                raise ErrorServicio(
                    "El objeto proporcionado no corresponde a un Servicio válido.",
                    detalles={"tipo": type(servicio).__name__},
                )
            if any(s.id == servicio.id for s in self.servicios):
                raise ErrorServicio(
                    f"Ya existe un servicio registrado con el ID '{servicio.id}'.",
                    detalles={"id_servicio": servicio.id},
                )
            self.servicios.append(servicio)
        except ErrorSistemaFJ as exc:
            self.logger.error(
                "Op #%d | Fallo registro servicio: %s | %s",
                self._contador_operaciones,
                exc.mensaje,
                exc.detalles,
            )
            raise
        else:
            self.logger.info(
                "Op #%d | Servicio registrado: %s",
                self._contador_operaciones,
                servicio.resumen(),
            )
            return servicio
        finally:
            self.logger.info(
                "Op #%d | Finalizó intento de registro de servicio.",
                self._contador_operaciones,
            )

    def buscar_cliente(self, id_cliente: str) -> Cliente:
        for cliente in self.clientes:
            if cliente.id == id_cliente.strip().upper():
                return cliente
        raise ErrorReserva(
            f"Cliente con ID '{id_cliente}' no encontrado.",
            detalles={"id_cliente": id_cliente},
        )

    def buscar_servicio(self, id_servicio: str) -> Servicio:
        for servicio in self.servicios:
            if servicio.id == id_servicio.strip().upper():
                return servicio
        raise ErrorReserva(
            f"Servicio con ID '{id_servicio}' no encontrado.",
            detalles={"id_servicio": id_servicio},
        )

    def crear_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
    ) -> Reserva:
        self._contador_operaciones += 1
        try:
            if any(r.id == id_reserva.strip().upper() for r in self.reservas):
                raise ErrorReserva(
                    f"Ya existe una reserva con el ID '{id_reserva}'.",
                    detalles={"id_reserva": id_reserva},
                )
            cliente = self.buscar_cliente(id_cliente)
            servicio = self.buscar_servicio(id_servicio)
            reserva = Reserva(
                id_reserva=id_reserva,
                cliente=cliente,
                servicio=servicio,
                duracion=duracion,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
            )
            self.reservas.append(reserva)
        except ErrorSistemaFJ as exc:
            self.logger.error(
                "Op #%d | Fallo al crear reserva: %s | %s",
                self._contador_operaciones,
                exc.mensaje,
                exc.detalles,
            )
            raise
        except Exception as exc:
            encadenada = ErrorReserva(
                f"Error inesperado al crear la reserva '{id_reserva}': {exc}",
                detalles={"id_reserva": id_reserva, "error_original": type(exc).__name__},
            )
            self.logger.error(
                "Op #%d | Error encadenado al crear reserva: %s",
                self._contador_operaciones,
                encadenada.mensaje,
            )
            raise encadenada from exc
        else:
            self.logger.info(
                "Op #%d | Reserva creada: %s",
                self._contador_operaciones,
                reserva.resumen(),
            )
            return reserva
        finally:
            self.logger.info(
                "Op #%d | Finalizó intento de creación de reserva.",
                self._contador_operaciones,
            )

    def procesar_flujo_reserva(
        self,
        id_reserva: str,
        confirmar_primero: bool = True,
        simular_fallo_calculo: bool = False,
    ) -> str:
        """Confirma (opcionalmente) y procesa una reserva con encadenamiento ante fallos."""
        self._contador_operaciones += 1
        try:
            reserva = next(
                (r for r in self.reservas if r.id == id_reserva.strip().upper()),
                None,
            )
            if reserva is None:
                raise ErrorReserva(
                    f"No se encontró la reserva '{id_reserva}' para procesar.",
                    detalles={"id_reserva": id_reserva},
                )

            if confirmar_primero and reserva.estado == EstadoReserva.PENDIENTE:
                reserva.confirmar()

            if simular_fallo_calculo:
                try:
                    _ = 10 / 0
                except ZeroDivisionError as exc:
                    raise ErrorCalculoCosto(
                        f"Inconsistencia matemática al procesar la reserva '{id_reserva}'.",
                        detalles={"id_reserva": id_reserva},
                    ) from exc

            mensaje_exito = reserva.procesar()
        except ErrorSistemaFJ as exc:
            self.logger.error(
                "Op #%d | Fallo al procesar reserva: %s | %s",
                self._contador_operaciones,
                exc.mensaje,
                exc.detalles,
            )
            raise
        else:
            self.logger.info("Op #%d | %s", self._contador_operaciones, mensaje_exito)
            return mensaje_exito
        finally:
            self.logger.info(
                "Op #%d | Finalizó procesamiento de reserva '%s'.",
                self._contador_operaciones,
                id_reserva,
            )

    def cancelar_reserva(self, id_reserva: str, motivo: str = "Cancelada por el usuario") -> None:
        self._contador_operaciones += 1
        try:
            reserva = next(
                (r for r in self.reservas if r.id == id_reserva.strip().upper()),
                None,
            )
            if reserva is None:
                raise ErrorReserva(
                    f"No se encontró la reserva '{id_reserva}' para cancelar.",
                    detalles={"id_reserva": id_reserva},
                )
            reserva.cancelar(motivo=motivo)
        except ErrorReserva as exc:
            self.logger.error(
                "Op #%d | Fallo al cancelar reserva: %s | %s",
                self._contador_operaciones,
                exc.mensaje,
                exc.detalles,
            )
            raise
        else:
            self.logger.info(
                "Op #%d | Reserva %s cancelada (%s).",
                self._contador_operaciones,
                id_reserva,
                motivo,
            )
        finally:
            self.logger.info(
                "Op #%d | Finalizó intento de cancelación de reserva '%s'.",
                self._contador_operaciones,
                id_reserva,
            )