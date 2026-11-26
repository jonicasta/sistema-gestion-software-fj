"""Simulación integral del sistema Software FJ (12 operaciones completas)."""

from entidades import Cliente
from excepciones import ErrorSistemaFJ
from reservas import SistemaGestionFJ
from servicios import AlquilerEquipo, AsesoriaEspecializada, ReservaSala


def ejecutar_operacion(titulo: str, accion, sistema: SistemaGestionFJ) -> None:
    """Ejecuta una operación de prueba capturando excepciones para mantener activo el sistema."""
    print(f"\n--- {titulo} ---")
    try:
        resultado = accion()
    except ErrorSistemaFJ as exc:
        print(f"[ERROR CONTROLADO | {exc.codigo}] {exc.mensaje}")
        if exc.__cause__ is not None:
            print(f"  ↳ Causa encadenada ({type(exc.__cause__).__name__}): {exc.__cause__}")
    except Exception as exc:
        print(f"[ERROR NO PREVISTO] {type(exc).__name__}: {exc}")
    else:
        if resultado is not None:
            print(f"[ÉXITO] {resultado}")
    finally:
        sistema.logger.info("Bloque finally ejecutado para: %s", titulo)


def main() -> None:
    sistema = SistemaGestionFJ(archivo_log="logs/sistema_fj.log")
    print("=== INICIO DE SIMULACIÓN - SISTEMA INTEGRAL SOFTWARE FJ ===")

    # 1. Registro válido de cliente particular
    ejecutar_operacion(
        "Operación 1: Registro de cliente válido (particular)",
        lambda: sistema.registrar_cliente(
            Cliente(
                "CLI-01",
                "Laura Méndez",
                "laura.mendez@correo.com",
                "3104567890",
                es_corporativo=False,
            )
        ),
        sistema,
    )

    # 2. Registro válido de cliente corporativo
    ejecutar_operacion(
        "Operación 2: Registro de cliente válido (corporativo)",
        lambda: sistema.registrar_cliente(
            Cliente(
                "CLI-02",
                "TechAndes SAS",
                "contacto@techandes.co",
                "6076543210",
                es_corporativo=True,
            )
        ),
        sistema,
    )

    # 3. Registro inválido de cliente (correo mal formado)
    ejecutar_operacion(
        "Operación 3: Intento de registro de cliente inválido (correo sin @/dominio)",
        lambda: sistema.registrar_cliente(
            Cliente("CLI-03", "Carlos Ruiz", "carlos_sin_correo", "3001112233")
        ),
        sistema,
    )

    # 4. Creación correcta de los 3 servicios especializados
    def registrar_tres_servicios():
        s1 = sistema.registrar_servicio(
            ReservaSala("SRV-SALA-1", "Sala Ejecutiva A", 80000, 12, disponible=True)
        )
        s2 = sistema.registrar_servicio(
            AlquilerEquipo("SRV-EQ-1", "Estación Workstation i7", 45000, 8, disponible=True)
        )
        s3 = sistema.registrar_servicio(
            AsesoriaEspecializada(
                "SRV-ASE-1",
                "Arquitectura Cloud",
                120000,
                "Cloud & DevOps",
                disponible=True,
            )
        )
        s4 = sistema.registrar_servicio(
            ReservaSala("SRV-SALA-2", "Auditorio Principal", 150000, 50, disponible=False)
        )
        return f"Servicios registrados: {s1.id}, {s2.id}, {s3.id}, {s4.id} (no disponible)"

    ejecutar_operacion(
        "Operación 4: Creación correcta de servicios especializados",
        registrar_tres_servicios,
        sistema,
    )

    # 5. Creación incorrecta de servicio (tarifa negativa / cero)
    ejecutar_operacion(
        "Operación 5: Creación incorrecta de servicio (tarifa inválida)",
        lambda: sistema.registrar_servicio(
            AlquilerEquipo("SRV-EQ-ERR", "Proyector 4K", -15000, 3)
        ),
        sistema,
    )

    # 6. Demostración de polimorfismo y sobrecarga en cálculo de costos
    def demostrar_polimorfismo_y_sobrecarga():
        sala = sistema.buscar_servicio("SRV-SALA-1")
        equipo = sistema.buscar_servicio("SRV-EQ-1")
        asesoria = sistema.buscar_servicio("SRV-ASE-1")

        descripciones = [srv.describir() for srv in (sala, equipo, asesoria)]

        c1 = sala.calcular_costo_sobrecargado(3)
        c2 = equipo.calcular_costo_sobrecargado(4.0)
        c3 = asesoria.calcular_costo_sobrecargado(
            {"cantidad": 5, "descuento_pct": 10.0, "impuesto_pct": 19.0}
        )
        return (
            f"{' | '.join(descripciones)} || Costos -> Sala(3h)=${c1:,.2f}, "
            f"Equipo(4d)=${c2:,.2f}, Asesoría(5h desc/IVA)=${c3:,.2f}"
        )

    ejecutar_operacion(
        "Operación 6: Polimorfismo y métodos sobrecargados de costo",
        demostrar_polimorfismo_y_sobrecarga,
        sistema,
    )

    # 7. Reserva exitosa y procesamiento completo
    def reserva_y_procesar_exitosa():
        res = sistema.crear_reserva(
            "RES-01", "CLI-01", "SRV-SALA-1", duracion=4, descuento_pct=5, impuesto_pct=19
        )
        return sistema.procesar_flujo_reserva(res.id, confirmar_primero=True)

    ejecutar_operacion(
        "Operación 7: Reserva exitosa confirmada y procesada",
        reserva_y_procesar_exitosa,
        sistema,
    )

    # 8. Reserva fallida por servicio no disponible
    ejecutar_operacion(
        "Operación 8: Reserva fallida (servicio no disponible)",
        lambda: sistema.crear_reserva("RES-02", "CLI-02", "SRV-SALA-2", duracion=2),
        sistema,
    )

    # 9. Reserva fallida por duración inválida (0 horas)
    ejecutar_operacion(
        "Operación 9: Reserva fallida (duración inválida)",
        lambda: sistema.crear_reserva("RES-03", "CLI-01", "SRV-ASE-1", duracion=0),
        sistema,
    )

    # 10. Reserva creada y luego cancelada correctamente
    def crear_y_cancelar():
        res = sistema.crear_reserva("RES-04", "CLI-02", "SRV-EQ-1", duracion=3)
        sistema.cancelar_reserva(res.id, motivo="Cambio de cronograma del cliente")
        return res.resumen()

    ejecutar_operacion(
        "Operación 10: Reserva creada y cancelada exitosamente",
        crear_y_cancelar,
        sistema,
    )

    # 11. Intento inválido de procesar una reserva cancelada
    ejecutar_operacion(
        "Operación 11: Intento inválido de procesar reserva cancelada (RES-04)",
        lambda: sistema.procesar_flujo_reserva("RES-04", confirmar_primero=False),
        sistema,
    )

    # 12. Encadenamiento de excepciones al forzar un error matemático durante procesamiento
    def provocar_encadenamiento():
        res = sistema.crear_reserva("RES-05", "CLI-02", "SRV-ASE-1", duracion=2)
        res.confirmar()
        return sistema.procesar_flujo_reserva(
            res.id,
            confirmar_primero=False,
            simular_fallo_calculo=True,
        )

    ejecutar_operacion(
        "Operación 12: Encadenamiento de excepciones en procesamiento",
        provocar_encadenamiento,
        sistema,
    )

    print("\n=== RESUMEN FINAL EN MEMORIA (SIN BASE DE DATOS) ===")
    print(f"Clientes registrados: {len(sistema.clientes)}")
    print(f"Servicios registrados: {len(sistema.servicios)}")
    print(f"Reservas registradas: {len(sistema.reservas)}")
    for r in sistema.reservas:
        print("  *", r.resumen())
    print("\nRevisa el archivo de registro en: logs/sistema_fj.log")


if __name__ == "__main__":
    main()