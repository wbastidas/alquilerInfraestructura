"""Siembra una base de datos de demostración con datos ficticios.

Sirve para probar el sistema completo (frontend incluido) sin depender de datos
reales de CNEL EP: crea las Unidades de Negocio, los 9 roles oficiales del §2.1,
un usuario por rol, dos operadoras, el catálogo de canon vigente (§6.12), y un
expediente completo por operadora —solicitud aprobada, contrato, alquiler anual
con desglose por zona, facturas con pagos y novedades— además de las alertas que
generan los jobs del §6.14.

    python -m scripts.sembrar_demo              # crea/actualiza ./demo_sgaie.db
    DATABASE_URL=... python -m scripts.sembrar_demo

TODOS los datos son inventados (RUC, cédulas, nombres y empresas): no
corresponden a personas ni operadoras reales.

Credenciales sembradas (todas con la misma clave, solo para demostración):

    admin / matriz / gye_admin / gye_tecnico / gye_gerente / gye_juridico /
    mil_admin / proveedor_teleandes / proveedor_fibraroja      →  Sgaie2026!
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Por defecto se siembra un SQLite local, para no exigir MariaDB en una demo.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parent.parent / 'demo_sgaie.db'}")

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import app.models  # noqa: F401,E402  (registra todos los modelos en Base.metadata)
from app.core.security import hashear_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SesionLocal, engine  # noqa: E402
from app.jobs.morosidad import marcar_facturas_vencidas  # noqa: E402
from app.jobs.vencimientos import detectar_vencimientos  # noqa: E402
from app.models.alquiler_anual import AlquilerAnual, PostePorZona  # noqa: E402
from app.models.cable_operadora import CableOperadora  # noqa: E402
from app.models.catalogo_canon import CatalogoCanon  # noqa: E402
from app.models.contrato import Contrato  # noqa: E402
from app.models.enums import (  # noqa: E402
    CoberturaGeografica,
    DirigidaA,
    EstadoContrato,
    EstadoContratoOperadora,
    EstadoNovedad,
    EstadoPago,
    EstadoSolicitud,
    MetodoPago,
    TipoCuenta,
    TipoNovedad,
    TipoPago,
    TipoSolicitud,
    TipoZona,
)
from app.models.novedad import Novedad  # noqa: E402
from app.models.pago import Factura, Pago  # noqa: E402
from app.models.rol import Rol  # noqa: E402
from app.models.solicitud import ContactoSolicitud, RutaPropuesta, Solicitud  # noqa: E402
from app.models.unidad_negocio import UnidadNegocio  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402
from app.services.alquiler_anual import sincronizar_recaudacion  # noqa: E402

CLAVE_DEMO = "Sgaie2026!"
HOY = date.today()
ANIO = HOY.year

ROLES = [
    ("SUPERADMIN", "Super Administrador"),
    ("MATRIZ_CONSULTA", "Matriz (solo lectura)"),
    ("UN_ADMIN", "Administrador de Unidad de Negocio"),
    ("UN_ADMIN_CONTRATO", "Administrador de Contratos de UN"),
    ("UN_DELEGADO_COORDINADOR", "Delegado Coordinador de UN"),
    ("UN_DELEGADO_TECNICO", "Delegado Técnico de UN"),
    ("UN_GERENTE", "Gerente de UN"),
    ("UN_JURIDICO", "Jurídico de UN"),
    ("PROVEEDOR", "Proveedor"),
]

CANONES = [
    (TipoZona.CAPITAL_PROVINCIAL, Decimal("9.00")),
    (TipoZona.CABECERA_CANTONAL, Decimal("7.02")),
    (TipoZona.OTRO_SECTOR, Decimal("6.03")),
]


def _crear_estructura(db: Session) -> tuple[UnidadNegocio, UnidadNegocio, dict[str, Rol]]:
    gye = UnidadNegocio(
        codigo="UN-GYE", nombre="CNEL EP Guayaquil", provincia="Guayas", activo=True
    )
    mil = UnidadNegocio(codigo="UN-MIL", nombre="CNEL EP Milagro", provincia="Guayas", activo=True)
    db.add_all([gye, mil])

    roles = {codigo: Rol(codigo=codigo, nombre=nombre) for codigo, nombre in ROLES}
    db.add_all(roles.values())

    for tipo_zona, valor in CANONES:
        db.add(
            CatalogoCanon(
                tipo_zona=tipo_zona,
                valor=valor,
                vigente_desde=date(2016, 1, 1),
                referencia_normativa="Oficio MEER-SDCE-2016-0181-OF (referencia ficticia)",
            )
        )
    db.commit()
    return gye, mil, roles


def _crear_operadora(
    db: Session,
    unidad_negocio: UnidadNegocio,
    numero_registro: str,
    nombre_empresa: str,
    ruc: str,
    representante: str,
    cedula: str,
    dias_para_vencer_titulo: int,
) -> CableOperadora:
    operadora = CableOperadora(
        numero_registro=numero_registro,
        nombre_empresa=nombre_empresa,
        ruc=ruc,
        representante_legal=representante,
        representante_cedula=cedula,
        titulo_habilitante_numero=f"ARCOTEL-{ANIO}-SVA-{numero_registro[-4:]}",
        titulo_habilitante_vigencia=HOY + timedelta(days=dias_para_vencer_titulo),
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        correo=f"contacto@{nombre_empresa.split()[0].lower()}.example.ec",
        estado_contrato=EstadoContratoOperadora.ACTIVO,
        unidad_negocio_id=unidad_negocio.id,
    )
    db.add(operadora)
    db.commit()
    return operadora


def _crear_usuarios(
    db: Session,
    roles: dict[str, Rol],
    gye: UnidadNegocio,
    mil: UnidadNegocio,
    teleandes: CableOperadora,
    fibraroja: CableOperadora,
) -> None:
    definiciones = [
        ("admin", "Ana Lucía Zambrano", "SUPERADMIN", None, None),
        ("matriz", "Marco Tulio Benítez", "MATRIZ_CONSULTA", None, None),
        ("gye_admin", "Gabriela Ycaza Moreira", "UN_ADMIN", gye.id, None),
        ("gye_tecnico", "Tomás Efraín Ronquillo", "UN_DELEGADO_TECNICO", gye.id, None),
        ("gye_gerente", "Genoveva Rivas Arteaga", "UN_GERENTE", gye.id, None),
        ("gye_juridico", "Julio César Mendoza", "UN_JURIDICO", gye.id, None),
        ("mil_admin", "Milton Andrés Salazar", "UN_ADMIN", mil.id, None),
        ("proveedor_teleandes", "María Elena Vera", "PROVEEDOR", gye.id, teleandes.id),
        ("proveedor_fibraroja", "Rodrigo Pazmiño Loor", "PROVEEDOR", mil.id, fibraroja.id),
    ]
    for username, nombre, rol, unidad_negocio_id, operadora_id in definiciones:
        db.add(
            Usuario(
                username=username,
                nombre_completo=nombre,
                correo=f"{username}@example.ec",
                tipo_cuenta=TipoCuenta.PROVEEDOR if rol == "PROVEEDOR" else TipoCuenta.LOCAL,
                password_hash=hashear_password(CLAVE_DEMO),
                rol_id=roles[rol].id,
                unidad_negocio_id=unidad_negocio_id,
                cable_operadora_id=operadora_id,
                activo=True,
            )
        )
    db.commit()


def _crear_expediente(
    db: Session,
    operadora: CableOperadora,
    unidad_negocio: UnidadNegocio,
    numero_solicitud: str,
    numero_contrato: str,
    postes: dict[TipoZona, int],
    dias_para_vencer_contrato: int,
    con_mora: bool,
) -> None:
    """Solicitud finalizada → contrato vigente → alquiler anual → facturas y pagos."""
    solicitud = Solicitud(
        numero_referencia=numero_solicitud,
        tipo=TipoSolicitud.NUEVO_CONTRATO,
        cable_operadora_id=operadora.id,
        unidad_negocio_id=unidad_negocio.id,
        cobertura=CoberturaGeografica.LOCAL,
        # Cobertura LOCAL ⇒ se dirige al Administrador de la UN (§9.4).
        dirigida_a=DirigidaA.ADMIN_UNIDAD_NEGOCIO,
        provincias_involucradas=unidad_negocio.provincia,
        postes_solicitados=sum(postes.values()),
        ductos_solicitados_m=Decimal("1500.00"),
        objetivo_proyecto="Despliegue de red de fibra óptica para servicio de internet fijo.",
        tipo_redes="Fibra óptica ADSS",
        estado=EstadoSolicitud.FINALIZADA,
        fecha_creacion=HOY - timedelta(days=120),
        cronograma_inicio=HOY - timedelta(days=90),
        cronograma_fin=HOY + timedelta(days=90),
    )
    solicitud.rutas_propuestas = [
        RutaPropuesta(
            provincia=unidad_negocio.provincia,
            ciudad=unidad_negocio.nombre.split()[-1],
            ruta="Troncal principal - ramales urbanos",
            postes_usados=sum(postes.values()) - 40,
            postes_nuevos=40,
            total_postes=sum(postes.values()),
        )
    ]
    solicitud.contactos = [
        ContactoSolicitud(
            rol_contacto="Responsable técnico",
            nombre="Jorge Andrés Peñafiel",
            telefono="0991234567",
            correo="tecnico@example.ec",
        )
    ]
    db.add(solicitud)
    db.commit()

    contrato = Contrato(
        cable_operadora_id=operadora.id,
        unidad_negocio_id=unidad_negocio.id,
        numero_contrato=numero_contrato,
        tipo_cobertura=CoberturaGeografica.LOCAL,
        estado=EstadoContrato.VIGENTE,
        fecha_suscripcion=HOY - timedelta(days=80),
        fecha_inicio=HOY - timedelta(days=80),
        fecha_fin=HOY + timedelta(days=dias_para_vencer_contrato),
        poliza_numero=f"POL-{numero_contrato[-6:]}",
        poliza_aseguradora="Seguros Equinoccio (ficticia)",
        poliza_valor=Decimal("18500.00"),
        poliza_vigencia_inicio=HOY - timedelta(days=80),
        poliza_vigencia_fin=HOY + timedelta(days=dias_para_vencer_contrato),
        solicitud_id=solicitud.id,
    )
    db.add(contrato)
    db.commit()

    canon_por_zona = {tipo: valor for tipo, valor in CANONES}
    zonas = [
        PostePorZona(
            provincia=unidad_negocio.provincia,
            canton=unidad_negocio.nombre.split()[-1],
            tipo_zona=tipo_zona,
            cantidad_postes=cantidad,
            canon_unitario=canon_por_zona[tipo_zona],
            subtotal=canon_por_zona[tipo_zona] * cantidad,
        )
        for tipo_zona, cantidad in postes.items()
    ]
    total_canon = sum((z.subtotal for z in zonas), Decimal("0"))

    alquiler = AlquilerAnual(
        cable_operadora_id=operadora.id,
        contrato_id=contrato.id,
        unidad_negocio_id=unidad_negocio.id,
        anio=ANIO,
        postes_sig=sum(postes.values()),
        # Discrepancia deliberada SIG vs. físico, para ver la alerta visual del frontend.
        postes_fisicos=sum(postes.values()) - 5,
        monto_facturado=total_canon,
        monto_recaudado=Decimal("0"),
        monto_pendiente_recaudar=total_canon,
        estado_pago=EstadoPago.PENDIENTE,
        fecha_facturacion=HOY - timedelta(days=60),
        postes_por_zona=zonas,
    )
    db.add(alquiler)
    db.commit()

    iva = (total_canon * Decimal("0.15")).quantize(Decimal("0.01"))
    factura = Factura(
        cable_operadora_id=operadora.id,
        contrato_id=contrato.id,
        alquiler_anual_id=alquiler.id,
        numero_factura=f"001-002-{alquiler.id:09d}",
        fecha_emision=HOY - timedelta(days=60),
        fecha_vencimiento=HOY - timedelta(days=30) if con_mora else HOY + timedelta(days=15),
        monto=total_canon,
        iva=iva,
        total=total_canon + iva,
    )
    db.add(factura)
    db.commit()

    # La operadora al día abona la mitad; la morosa no ha pagado nada.
    if not con_mora:
        db.add(
            Pago(
                factura_id=factura.id,
                cable_operadora_id=operadora.id,
                monto=((total_canon + iva) / 2).quantize(Decimal("0.01")),
                tipo=TipoPago.PARCIAL,
                metodo=MetodoPago.TRANSFERENCIA,
                referencia_transaccion="TRX-DEMO-0001",
                fecha_pago=HOY - timedelta(days=20),
                conciliado=True,
                fecha_conciliacion=HOY - timedelta(days=19),
            )
        )
        db.commit()
        sincronizar_recaudacion(db, alquiler.id)
        db.commit()

    db.add(
        Novedad(
            cable_operadora_id=operadora.id,
            contrato_id=contrato.id,
            unidad_negocio_id=unidad_negocio.id,
            tipo=TipoNovedad.INSPECCION_PROGRAMADA,
            descripcion="Inspección de cableado y estado de placas de identificación.",
            estado=EstadoNovedad.PROGRAMADA,
            fecha_programada=HOY + timedelta(days=7),
            latitud=Decimal("-2.1709979"),
            longitud=Decimal("-79.9223592"),
        )
    )
    db.commit()


def sembrar() -> None:
    if db_ya_sembrada():
        print("La base ya contiene datos: se aborta para no duplicar el escenario.")
        print("Borra el archivo demo_sgaie.db (o vacía la base) y vuelve a ejecutar.")
        sys.exit(1)

    Base.metadata.create_all(engine)
    with SesionLocal() as db:
        gye, mil, roles = _crear_estructura(db)

        teleandes = _crear_operadora(
            db, gye, "REG-GYE-0007", "TeleAndes Fibra S.A.", "0992123456001",
            "María Elena Vera Cedeño", "0912345678", dias_para_vencer_titulo=20,
        )
        fibraroja = _crear_operadora(
            db, mil, "REG-MIL-0012", "FibraRoja Networks Cía. Ltda.", "0993987654001",
            "Rodrigo Pazmiño Loor", "0923456789", dias_para_vencer_titulo=300,
        )

        _crear_usuarios(db, roles, gye, mil, teleandes, fibraroja)

        _crear_expediente(
            db, teleandes, gye, f"SOL-{ANIO}-00001", f"CNT-GYE-{ANIO}-014",
            {TipoZona.CAPITAL_PROVINCIAL: 300, TipoZona.CABECERA_CANTONAL: 100,
             TipoZona.OTRO_SECTOR: 20},
            dias_para_vencer_contrato=25,  # dentro de la ventana de alerta (§6.14)
            con_mora=False,
        )
        _crear_expediente(
            db, fibraroja, mil, f"SOL-{ANIO}-00002", f"CNT-MIL-{ANIO}-003",
            {TipoZona.CABECERA_CANTONAL: 180, TipoZona.OTRO_SECTOR: 60},
            dias_para_vencer_contrato=400,
            con_mora=True,
        )

        # Jobs del §6.14: dejan el tablero con facturas vencidas y alertas reales.
        vencidas = marcar_facturas_vencidas(db)
        db.commit()
        alertas = detectar_vencimientos(db)
        db.commit()

        print("Base de demostración creada.")
        print(f"  Unidades de negocio : 2      Operadoras: 2      Usuarios: 9")
        print(f"  Facturas marcadas vencidas: {len(vencidas)}")
        print(f"  Alertas de vencimiento generadas: {len(alertas)}")
        print(f"\n  Usuarios (clave común: {CLAVE_DEMO}):")
        for usuario in db.scalars(select(Usuario).order_by(Usuario.id)):
            print(f"    {usuario.username:22} {usuario.nombre_completo}")


def db_ya_sembrada() -> bool:
    try:
        with SesionLocal() as db:
            return db.scalar(select(UnidadNegocio).limit(1)) is not None
    except Exception:
        return False


if __name__ == "__main__":
    sembrar()
