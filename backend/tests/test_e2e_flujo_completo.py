"""Prueba end-to-end del ciclo de vida completo del sistema con datos ficticios.

A diferencia del resto de la suite (que prueba cada servicio de forma aislada),
este módulo recorre **todas las etapas del negocio en orden**, siempre a través
de la API HTTP y con tokens JWT reales, tal como lo haría un usuario:

    catálogo de canon → operadora → solicitud → checklist documental (§11) →
    workflow de autorizaciones (§7.5, §8) → contrato → alquiler anual (§7.2) →
    factura y pagos (§7.4) → morosidad → novedades (§7.6) → alertas y
    dashboard (§6.14, §7.2)

Todos los datos son ficticios (operadora "TeleAndes Fibra S.A.", cédulas/RUC
inventados) y viven en la BD SQLite en memoria de la fixture `db_session`.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hashear_password
from app.jobs.morosidad import marcar_facturas_vencidas
from app.jobs.vencimientos import detectar_vencimientos
from app.middlewares.rate_limit import limiter
from app.models.cable_operadora import CableOperadora
from app.models.enums import (
    CoberturaGeografica,
    EstadoContratoOperadora,
    TipoCuenta,
)
from app.models.rol import Rol
from app.models.unidad_negocio import UnidadNegocio
from app.models.usuario import Usuario

API = "/api/v1"

# §11: los 11 tipos de documento que el proveedor debe entregar para que la
# solicitud pueda pasar de Revisión Técnica a Aprobación Gerencial.
TIPOS_CHECKLIST = [
    "SOLICITUD_FORMAL",
    "TITULO_HABILITANTE",
    "DOC_SOCIETARIA",
    "RUC",
    "CEDULA_REP_LEGAL",
    "COMPROBANTE_PAGO_ENERGIA",
    "POLIZA",
    "PLAN_EXPANSION",
    "SIG_GEODATABASE",
    "ESPEC_TECNICAS",
    "LISTADO_CONTACTOS",
]

PDF_FICTICIO = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
JPG_FICTICIO = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 64 + b"\xff\xd9"

CLAVE = "Sgaie2026!"


@pytest.fixture(autouse=True)
def _sin_rate_limit():
    """El recorrido completo hace más logins que el límite de 5/minuto del §4.3.

    El rate limiting ya tiene su propia cobertura; aquí estorbaría al flujo de
    negocio, así que se desactiva solo durante estas pruebas.
    """
    limiter.enabled = False
    yield
    limiter.enabled = True
    limiter.reset()


@pytest.fixture()
def escenario(db_session: Session, directorio_documentos):
    """Datos ficticios de partida: dos UN, los roles del §2.1, usuarios y una operadora."""
    gye = UnidadNegocio(codigo="UN-GYE", nombre="CNEL EP Guayaquil", provincia="Guayas", activo=True)
    mil = UnidadNegocio(codigo="UN-MIL", nombre="CNEL EP Milagro", provincia="Guayas", activo=True)
    db_session.add_all([gye, mil])
    db_session.commit()

    codigos_rol = [
        "SUPERADMIN",
        "MATRIZ_CONSULTA",
        "UN_ADMIN",
        "UN_DELEGADO_TECNICO",
        "UN_GERENTE",
        "UN_JURIDICO",
        "PROVEEDOR",
    ]
    roles = {codigo: Rol(codigo=codigo, nombre=codigo.title()) for codigo in codigos_rol}
    db_session.add_all(roles.values())
    db_session.commit()

    operadora = CableOperadora(
        numero_registro="REG-GYE-0007",
        nombre_empresa="TeleAndes Fibra S.A.",
        ruc="0992123456001",
        representante_legal="María Elena Vera Cedeño",
        representante_cedula="0912345678",
        titulo_habilitante_numero="ARCOTEL-2024-SVA-0421",
        titulo_habilitante_vigencia=date.today() + timedelta(days=20),
        cobertura_geografica=CoberturaGeografica.LOCAL,
        tipo_contrato=CoberturaGeografica.LOCAL,
        correo="contacto@teleandes.example.ec",
        estado_contrato=EstadoContratoOperadora.ACTIVO,
        unidad_negocio_id=gye.id,
    )
    db_session.add(operadora)
    db_session.commit()

    def _usuario(username: str, rol: str, un_id: int | None, operadora_id: int | None = None):
        usuario = Usuario(
            username=username,
            nombre_completo=f"Usuario {username}",
            correo=f"{username}@example.ec",
            tipo_cuenta=TipoCuenta.PROVEEDOR if rol == "PROVEEDOR" else TipoCuenta.LOCAL,
            password_hash=hashear_password(CLAVE),
            rol_id=roles[rol].id,
            unidad_negocio_id=un_id,
            cable_operadora_id=operadora_id,
            activo=True,
        )
        db_session.add(usuario)
        return usuario

    _usuario("admin", "SUPERADMIN", None)
    _usuario("matriz", "MATRIZ_CONSULTA", None)
    _usuario("gye_admin", "UN_ADMIN", gye.id)
    _usuario("gye_tecnico", "UN_DELEGADO_TECNICO", gye.id)
    _usuario("gye_gerente", "UN_GERENTE", gye.id)
    _usuario("gye_juridico", "UN_JURIDICO", gye.id)
    _usuario("mil_admin", "UN_ADMIN", mil.id)
    _usuario("proveedor", "PROVEEDOR", gye.id, operadora.id)
    db_session.commit()

    return {"gye": gye, "mil": mil, "operadora": operadora}


def _token(cliente: TestClient, username: str) -> dict[str, str]:
    """Login real por HTTP: devuelve la cabecera Authorization lista para usar."""
    respuesta = cliente.post(f"{API}/auth/login", json={"username": username, "password": CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def test_flujo_completo_de_negocio(cliente_api: TestClient, db_session: Session, escenario):
    """Recorre todas las etapas del sistema, de la solicitud al cobro y las alertas."""
    operadora_id = escenario["operadora"].id
    gye_id = escenario["gye"].id

    assert cliente_api.get(f"{API}/salud").json() == {"estado": "ok"}

    admin = _token(cliente_api, "admin")
    proveedor = _token(cliente_api, "proveedor")
    tecnico = _token(cliente_api, "gye_tecnico")
    gerente = _token(cliente_api, "gye_gerente")
    juridico = _token(cliente_api, "gye_juridico")
    un_admin = _token(cliente_api, "gye_admin")

    # --- Etapa 1: catálogo de canon vigente (§6.12), base del cálculo del alquiler ---
    canones = {
        "CAPITAL_PROVINCIAL": "12.50",
        "CABECERA_CANTONAL": "9.00",
        "OTRO_SECTOR": "6.25",
    }
    for tipo_zona, valor in canones.items():
        respuesta = cliente_api.post(
            f"{API}/catalogo-canon",
            headers=admin,
            json={
                "tipo_zona": tipo_zona,
                "valor": valor,
                "vigente_desde": str(date(date.today().year, 1, 1)),
                "referencia_normativa": "Resolución ficticia ARCOTEL-CNEL-2026-001",
            },
        )
        assert respuesta.status_code == 201, respuesta.text

    # --- Etapa 2: el proveedor crea su solicitud de nuevo contrato (§6.7) ---
    respuesta = cliente_api.post(
        f"{API}/solicitudes",
        headers=proveedor,
        json={
            "cable_operadora_id": operadora_id,
            "tipo": "NUEVO_CONTRATO",
            "cobertura": "LOCAL",
            "provincias_involucradas": "Guayas",
            "postes_solicitados": 420,
            "ductos_solicitados_m": "1500.00",
            "objetivo_proyecto": "Despliegue de red FTTH en el norte de Guayaquil.",
            "tipo_redes": "Fibra óptica ADSS",
            "cronograma_inicio": str(date.today() + timedelta(days=30)),
            "cronograma_fin": str(date.today() + timedelta(days=210)),
            "rutas_propuestas": [
                {
                    "provincia": "Guayas",
                    "ciudad": "Guayaquil",
                    "ruta": "Av. Francisco de Orellana - Av. Plaza Dañín",
                    "postes_usados": 300,
                    "postes_nuevos": 120,
                    "total_postes": 420,
                }
            ],
            "contactos": [
                {
                    "rol_contacto": "Responsable técnico",
                    "nombre": "Jorge Andrés Peñafiel",
                    "telefono": "0991234567",
                    "correo": "jpenafiel@teleandes.example.ec",
                }
            ],
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    solicitud = respuesta.json()
    solicitud_id = solicitud["id"]
    assert solicitud["estado"] == "BORRADOR"
    assert solicitud["numero_referencia"].startswith(f"SOL-{date.today().year}-")
    # Cobertura LOCAL ⇒ la solicitud se dirige al Administrador de la UN (§9.4).
    assert solicitud["dirigida_a"] == "ADMIN_UNIDAD_NEGOCIO"
    assert solicitud["unidad_negocio_id"] == gye_id

    # --- Etapa 3: checklist documental del §11 ---
    documentos_por_tipo: dict[str, int] = {}
    for tipo in TIPOS_CHECKLIST:
        respuesta = cliente_api.post(
            f"{API}/documentos",
            headers=proveedor,
            data={"solicitud_id": solicitud_id, "tipo_documento": tipo},
            files={"archivo": (f"{tipo.lower()}.pdf", PDF_FICTICIO, "application/pdf")},
        )
        assert respuesta.status_code == 201, respuesta.text
        documentos_por_tipo[tipo] = respuesta.json()["id"]
        # El hash SHA-256 se calcula al guardar (§4.8, integridad del expediente).
        assert len(respuesta.json()["hash_sha256"]) == 64

    checklist = cliente_api.get(
        f"{API}/solicitudes/{solicitud_id}/checklist", headers=proveedor
    ).json()
    assert len(checklist) == 11
    assert all(item["estado_validacion"] == "PENDIENTE" for item in checklist)

    # Un archivo con extensión no permitida debe rechazarse (§4.8).
    respuesta = cliente_api.post(
        f"{API}/documentos",
        headers=proveedor,
        data={"solicitud_id": solicitud_id, "tipo_documento": "OTRO"},
        files={"archivo": ("malicioso.exe", b"MZ\x90\x00", "application/x-msdownload")},
    )
    assert respuesta.status_code == 400

    # --- Etapa 4: envío y workflow de autorizaciones (§7.5, §8) ---
    respuesta = cliente_api.post(f"{API}/solicitudes/{solicitud_id}/enviar", headers=proveedor)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "RECEPCION"

    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=tecnico,
        json={"estado": "APROBADO", "comentario": "Documentación recibida conforme."},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "REVISION_TECNICA"

    # Compuerta documental del §11: sin los 11 documentos VALIDADOS no se avanza.
    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=tecnico,
        json={"estado": "APROBADO"},
    )
    assert respuesta.status_code == 409, respuesta.text
    assert "documental" in respuesta.json()["detail"].lower()

    for documento_id in documentos_por_tipo.values():
        respuesta = cliente_api.post(
            f"{API}/documentos/{documento_id}/validar",
            headers=tecnico,
            json={"estado_validacion": "VALIDADO"},
        )
        assert respuesta.status_code == 200, respuesta.text

    checklist = cliente_api.get(
        f"{API}/solicitudes/{solicitud_id}/checklist", headers=tecnico
    ).json()
    assert all(item["estado_validacion"] == "VALIDADO" for item in checklist)

    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=tecnico,
        json={"estado": "APROBADO", "comentario": "Factibilidad técnica favorable."},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "APROBACION_GERENCIAL"

    # Camino de observación y subsanación (§8): OBSERVADA → editar → reenviar.
    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=gerente,
        json={"estado": "OBSERVADO", "comentario": "Precisar el cronograma de puesta en servicio."},
    )
    assert respuesta.json()["estado"] == "OBSERVADA"

    respuesta = cliente_api.put(
        f"{API}/solicitudes/{solicitud_id}",
        headers=proveedor,
        json={"puesta_en_servicio": str(date.today() + timedelta(days=240))},
    )
    assert respuesta.status_code == 200, respuesta.text

    respuesta = cliente_api.post(f"{API}/solicitudes/{solicitud_id}/reenviar", headers=proveedor)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "APROBACION_GERENCIAL"

    for actor, esperado in (
        (gerente, "REVISION_JURIDICA"),
        (juridico, "AUTORIZACION_FINAL"),
        (un_admin, "FINALIZADA"),
    ):
        respuesta = cliente_api.post(
            f"{API}/solicitudes/{solicitud_id}/decidir",
            headers=actor,
            json={"estado": "APROBADO"},
        )
        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["estado"] == esperado

    autorizaciones = cliente_api.get(
        f"{API}/solicitudes/{solicitud_id}/autorizaciones", headers=un_admin
    ).json()
    etapas = [a["etapa"] for a in autorizaciones]
    assert etapas == [
        "RECEPCION",
        "REVISION_TECNICA",
        "APROBACION_GERENCIAL",
        "APROBACION_GERENCIAL",
        "REVISION_JURIDICA",
        "AUTORIZACION_FINAL",
    ]

    # --- Etapa 5: contrato derivado de la solicitud aprobada (§6.5) ---
    respuesta = cliente_api.post(
        f"{API}/contratos",
        headers=un_admin,
        json={
            "cable_operadora_id": operadora_id,
            "unidad_negocio_id": gye_id,
            "numero_contrato": "CNT-GYE-2026-014",
            "tipo_cobertura": "LOCAL",
            "fecha_suscripcion": str(date.today()),
            "fecha_inicio": str(date.today()),
            "fecha_fin": str(date.today() + timedelta(days=20)),
            "poliza_numero": "POL-778812",
            "poliza_aseguradora": "Seguros Equinoccio (ficticia)",
            "poliza_valor": "18500.00",
            "poliza_vigencia_inicio": str(date.today()),
            "poliza_vigencia_fin": str(date.today() + timedelta(days=15)),
            "solicitud_id": solicitud_id,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    contrato_id = respuesta.json()["id"]
    # Nace EN_JURIDICO: jurídico lo redacta a partir del modelo base y solo pasa
    # a VIGENTE una vez suscrito (§7.3).
    assert respuesta.json()["estado"] == "EN_JURIDICO"

    # Transición inválida: no se puede saltar directo a TERMINADO.
    respuesta = cliente_api.put(
        f"{API}/contratos/{contrato_id}", headers=juridico, json={"estado": "TERMINADO"}
    )
    assert respuesta.status_code == 409

    respuesta = cliente_api.put(
        f"{API}/contratos/{contrato_id}", headers=juridico, json={"estado": "VIGENTE"}
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "VIGENTE"

    # --- Etapa 6: alquiler anual con desglose por zona y canon calculado (§7.2) ---
    respuesta = cliente_api.post(
        f"{API}/alquileres-anuales",
        headers=un_admin,
        json={
            "cable_operadora_id": operadora_id,
            "contrato_id": contrato_id,
            "unidad_negocio_id": gye_id,
            "anio": date.today().year,
            "postes_sig": 420,
            "postes_fisicos": 415,
            "postes_por_zona": [
                {
                    "provincia": "Guayas",
                    "canton": "Guayaquil",
                    "tipo_zona": "CAPITAL_PROVINCIAL",
                    "cantidad_postes": 300,
                },
                {
                    "provincia": "Guayas",
                    "canton": "Durán",
                    "tipo_zona": "CABECERA_CANTONAL",
                    "cantidad_postes": 100,
                },
                {
                    "provincia": "Guayas",
                    "canton": "Nobol",
                    "tipo_zona": "OTRO_SECTOR",
                    "cantidad_postes": 20,
                },
            ],
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    alquiler = respuesta.json()
    alquiler_id = alquiler["id"]
    # 300×12.50 + 100×9.00 + 20×6.25 = 3750 + 900 + 125 = 4775.00
    esperado = Decimal("300") * Decimal("12.50") + Decimal("100") * Decimal("9.00") + Decimal(
        "20"
    ) * Decimal("6.25")
    assert Decimal(alquiler["monto_facturado"]) == esperado == Decimal("4775.00")
    assert Decimal(alquiler["monto_pendiente_recaudar"]) == esperado
    assert alquiler["estado_pago"] == "PENDIENTE"

    # --- Etapa 7: facturación y recaudación (§7.4) ---
    respuesta = cliente_api.post(
        f"{API}/facturas",
        headers=un_admin,
        json={
            "cable_operadora_id": operadora_id,
            "contrato_id": contrato_id,
            "alquiler_anual_id": alquiler_id,
            "numero_factura": "001-002-000004775",
            "fecha_emision": str(date.today()),
            "fecha_vencimiento": str(date.today() + timedelta(days=30)),
            "monto": "4775.00",
            "iva": "716.25",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    factura = respuesta.json()
    factura_id = factura["id"]
    assert Decimal(factura["total"]) == Decimal("5491.25")
    assert factura["estado"] == "EMITIDA"

    respuesta = cliente_api.post(
        f"{API}/pagos",
        headers=un_admin,
        json={
            "factura_id": factura_id,
            "monto": "2000.00",
            "tipo": "PARCIAL",
            "metodo": "TRANSFERENCIA",
            "referencia_transaccion": "TRX-FICTICIA-0001",
            "fecha_pago": str(date.today()),
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    pago_parcial_id = respuesta.json()["id"]
    assert respuesta.json()["conciliado"] is False

    factura = cliente_api.get(f"{API}/facturas/{factura_id}", headers=un_admin).json()
    assert factura["estado"] == "PARCIAL"

    respuesta = cliente_api.post(f"{API}/pagos/{pago_parcial_id}/conciliar", headers=un_admin)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["conciliado"] is True

    respuesta = cliente_api.post(
        f"{API}/pagos",
        headers=un_admin,
        json={
            "factura_id": factura_id,
            "monto": "3491.25",
            "tipo": "TOTAL",
            "metodo": "TRANSFERENCIA",
            "referencia_transaccion": "TRX-FICTICIA-0002",
            "fecha_pago": str(date.today()),
        },
    )
    assert respuesta.status_code == 201, respuesta.text

    factura = cliente_api.get(f"{API}/facturas/{factura_id}", headers=un_admin).json()
    assert factura["estado"] == "PAGADA"
    assert len(factura["pagos"]) == 2

    # El cobro se refleja en el alquiler anual, neto de IVA: el canon del §6.12
    # no lleva impuestos, así que de los 5491.25 cobrados 4775.00 son arriendo.
    alquiler = cliente_api.get(f"{API}/alquileres-anuales/{alquiler_id}", headers=un_admin).json()
    assert Decimal(alquiler["monto_recaudado"]) == Decimal("4775.00")
    assert Decimal(alquiler["monto_pendiente_recaudar"]) == Decimal("0.00")
    assert alquiler["estado_pago"] == "COMPLETO"

    # --- Etapa 8: morosidad (§6.14) sobre una segunda factura ya vencida ---
    respuesta = cliente_api.post(
        f"{API}/facturas",
        headers=un_admin,
        json={
            "cable_operadora_id": operadora_id,
            "contrato_id": contrato_id,
            "alquiler_anual_id": alquiler_id,
            "numero_factura": "001-002-000004776",
            "fecha_emision": str(date.today() - timedelta(days=90)),
            "fecha_vencimiento": str(date.today() - timedelta(days=45)),
            "monto": "1000.00",
            "iva": "0",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    factura_vencida_id = respuesta.json()["id"]

    vencidas = marcar_facturas_vencidas(db_session)
    db_session.commit()
    assert factura_vencida_id in [f.id for f in vencidas]

    morosidad = cliente_api.get(f"{API}/facturas/morosidad", headers=un_admin).json()
    item = next(m for m in morosidad if m["factura_id"] == factura_vencida_id)
    assert item["dias_mora"] >= 45
    assert Decimal(item["saldo_pendiente"]) == Decimal("1000.00")
    assert Decimal(item["interes_mora"]) > 0

    # --- Etapa 9: novedades en campo (§7.6) ---
    respuesta = cliente_api.post(
        f"{API}/novedades",
        headers=tecnico,
        json={
            "cable_operadora_id": operadora_id,
            "contrato_id": contrato_id,
            "unidad_negocio_id": gye_id,
            "tipo": "INSPECCION_PROGRAMADA",
            "descripcion": "Inspección de cableado en Av. Plaza Dañín.",
            "fecha_programada": str(date.today()),
            "latitud": "-2.1709979",
            "longitud": "-79.9223592",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    novedad_id = respuesta.json()["id"]
    assert respuesta.json()["estado"] == "PROGRAMADA"

    for estado in ("EN_PROCESO", "EJECUTADA", "CERRADA"):
        respuesta = cliente_api.put(
            f"{API}/novedades/{novedad_id}", headers=tecnico, json={"estado": estado}
        )
        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json()["estado"] == estado

    # Estado terminal: no se puede retroceder (§7.6).
    respuesta = cliente_api.put(
        f"{API}/novedades/{novedad_id}", headers=tecnico, json={"estado": "EN_PROCESO"}
    )
    assert respuesta.status_code == 409

    respuesta = cliente_api.post(
        f"{API}/novedades/{novedad_id}/fotografias",
        headers=tecnico,
        data={"latitud": "-2.1709979", "longitud": "-79.9223592"},
        files={"archivo": ("evidencia.jpg", JPG_FICTICIO, "image/jpeg")},
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["novedad_id"] == novedad_id

    # --- Etapa 10: alertas de vencimiento y dashboard (§6.14, §7.2) ---
    alertas_generadas = detectar_vencimientos(db_session)
    db_session.commit()
    tipos_alerta = {a.tipo.value for a in alertas_generadas}
    # Contrato, póliza y título habilitante vencen dentro de la ventana de 30 días.
    assert {"VENCIMIENTO_CONTRATO", "VENCIMIENTO_POLIZA", "VENCIMIENTO_TITULO"} <= tipos_alerta

    # El job es idempotente: una segunda corrida no duplica alertas.
    assert detectar_vencimientos(db_session) == []

    alertas = cliente_api.get(f"{API}/alertas", headers=un_admin).json()
    assert len(alertas) >= 3
    assert all(a["leida"] is False for a in alertas)

    respuesta = cliente_api.patch(f"{API}/alertas/{alertas[0]['id']}/leida", headers=un_admin)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["leida"] is True

    consolidado = cliente_api.get(f"{API}/dashboard/consolidado", headers=un_admin).json()
    assert consolidado["total_operadoras"] == 1
    assert consolidado["total_contratos_vigentes"] == 1
    assert Decimal(consolidado["monto_facturado"]) == Decimal("4775.00")
    assert Decimal(consolidado["monto_recaudado"]) == Decimal("4775.00")
    assert consolidado["facturas_vencidas"] == 1
    assert consolidado["novedades_abiertas"] == 0
    assert consolidado["alertas_no_leidas"] == len(alertas) - 1


def test_alcance_por_rol_en_el_flujo(cliente_api: TestClient, db_session: Session, escenario):
    """La regla de oro del §5.2/§5.3 se sostiene sobre los datos del flujo real."""
    operadora_id = escenario["operadora"].id
    gye_id = escenario["gye"].id

    proveedor = _token(cliente_api, "proveedor")
    matriz = _token(cliente_api, "matriz")
    mil_admin = _token(cliente_api, "mil_admin")
    tecnico = _token(cliente_api, "gye_tecnico")

    respuesta = cliente_api.post(
        f"{API}/solicitudes",
        headers=proveedor,
        json={
            "cable_operadora_id": operadora_id,
            "tipo": "NUEVO_CONTRATO",
            "cobertura": "LOCAL",
            "postes_solicitados": 10,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    solicitud_id = respuesta.json()["id"]

    # Matriz: lectura global, escritura prohibida.
    assert cliente_api.get(f"{API}/solicitudes/{solicitud_id}", headers=matriz).status_code == 200
    respuesta = cliente_api.post(
        f"{API}/solicitudes",
        headers=matriz,
        json={"cable_operadora_id": operadora_id, "tipo": "NUEVO_CONTRATO", "cobertura": "LOCAL"},
    )
    assert respuesta.status_code == 403

    # Otra Unidad de Negocio no ve el expediente de Guayaquil (§5.2). El acceso
    # directo se rechaza con 403 y el listado simplemente no lo incluye.
    assert cliente_api.get(f"{API}/solicitudes/{solicitud_id}", headers=mil_admin).status_code == 403
    assert cliente_api.get(f"{API}/solicitudes", headers=mil_admin).json() == []

    # El proveedor no participa en las decisiones del workflow interno.
    cliente_api.post(f"{API}/solicitudes/{solicitud_id}/enviar", headers=proveedor)
    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=proveedor,
        json={"estado": "APROBADO"},
    )
    assert respuesta.status_code == 403

    # El proveedor tampoco puede emitir su propia factura (integridad financiera, §7.4).
    respuesta = cliente_api.post(
        f"{API}/facturas",
        headers=proveedor,
        json={
            "cable_operadora_id": operadora_id,
            "contrato_id": 1,
            "alquiler_anual_id": 1,
            "numero_factura": "FALSA-001",
            "fecha_emision": str(date.today()),
            "fecha_vencimiento": str(date.today()),
            "monto": "1.00",
        },
    )
    assert respuesta.status_code == 403

    # Una novedad de Guayaquil no puede registrarse contra otra UN.
    respuesta = cliente_api.post(
        f"{API}/novedades",
        headers=tecnico,
        json={
            "cable_operadora_id": operadora_id,
            "unidad_negocio_id": escenario["mil"].id,
            "tipo": "DANO_REPORTADO",
        },
    )
    assert respuesta.status_code in (403, 404)

    # Sin token no se accede a nada.
    assert cliente_api.get(f"{API}/solicitudes").status_code == 401
    assert gye_id  # el escenario se construyó sobre la UN de Guayaquil


def test_expediente_cerrado_no_admite_nuevos_documentos(
    cliente_api: TestClient, db_session: Session, escenario
):
    """Una solicitud ya decidida no acepta cargas: el checklist es el sustento
    de esa decisión (§11) y alterarlo rompería la trazabilidad del workflow."""
    operadora_id = escenario["operadora"].id
    proveedor = _token(cliente_api, "proveedor")
    tecnico = _token(cliente_api, "gye_tecnico")

    respuesta = cliente_api.post(
        f"{API}/solicitudes",
        headers=proveedor,
        json={
            "cable_operadora_id": operadora_id,
            "tipo": "NUEVO_CONTRATO",
            "cobertura": "LOCAL",
            "postes_solicitados": 10,
        },
    )
    solicitud_id = respuesta.json()["id"]

    def _subir():
        return cliente_api.post(
            f"{API}/documentos",
            headers=proveedor,
            data={"solicitud_id": solicitud_id, "tipo_documento": "RUC"},
            files={"archivo": ("ruc.pdf", PDF_FICTICIO, "application/pdf")},
        )

    # En BORRADOR se arma el expediente: la carga es válida.
    assert _subir().status_code == 201

    cliente_api.post(f"{API}/solicitudes/{solicitud_id}/enviar", headers=proveedor)
    # También durante el workflow, para subsanar lo que pida el revisor.
    assert _subir().status_code == 201

    # Rechazada: expediente cerrado.
    respuesta = cliente_api.post(
        f"{API}/solicitudes/{solicitud_id}/decidir",
        headers=tecnico,
        json={"estado": "RECHAZADO", "comentario": "No cumple requisitos técnicos."},
    )
    assert respuesta.json()["estado"] == "RECHAZADA"

    respuesta = _subir()
    assert respuesta.status_code == 409
    assert "no admite" in respuesta.json()["detail"].lower()
