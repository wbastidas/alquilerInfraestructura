"""Pruebas de RBAC (§5.2, §5.3): regla de oro Matriz=lectura global, UN=propia, Proveedor=propio."""

import pytest
from fastapi import HTTPException

from app.auth.deps import UsuarioContexto, filtro_unidad_negocio, requerir_escritura, requerir_roles


def _contexto(rol: str, unidad_negocio_id: int | None = None) -> UsuarioContexto:
    return UsuarioContexto(
        id=1, username="u", rol=rol, unidad_negocio_id=unidad_negocio_id, tipo_cuenta="LOCAL"
    )


def test_es_matriz_o_superadmin_para_matriz_y_superadmin():
    assert _contexto("MATRIZ_CONSULTA").es_matriz_o_superadmin
    assert _contexto("SUPERADMIN").es_matriz_o_superadmin
    assert not _contexto("UN_OPERADOR", 1).es_matriz_o_superadmin


def test_es_proveedor():
    assert _contexto("PROVEEDOR").es_proveedor
    assert not _contexto("UN_OPERADOR", 1).es_proveedor


def test_requerir_roles_permite_rol_autorizado():
    verificador = requerir_roles("SUPERADMIN", "MATRIZ_CONSULTA")
    usuario = _contexto("SUPERADMIN")
    assert verificador(usuario) is usuario


def test_requerir_roles_rechaza_rol_no_autorizado():
    verificador = requerir_roles("SUPERADMIN")
    with pytest.raises(HTTPException) as exc_info:
        verificador(_contexto("UN_OPERADOR", 1))
    assert exc_info.value.status_code == 403


def test_requerir_escritura_bloquea_matriz_consulta():
    with pytest.raises(HTTPException) as exc_info:
        requerir_escritura(_contexto("MATRIZ_CONSULTA"))
    assert exc_info.value.status_code == 403


def test_requerir_escritura_permite_superadmin_y_un():
    superadmin = _contexto("SUPERADMIN")
    un_usuario = _contexto("UN_OPERADOR", 1)
    assert requerir_escritura(superadmin) is superadmin
    assert requerir_escritura(un_usuario) is un_usuario


def test_filtro_unidad_negocio_global_para_matriz_y_superadmin():
    assert filtro_unidad_negocio(_contexto("MATRIZ_CONSULTA")) is None
    assert filtro_unidad_negocio(_contexto("SUPERADMIN")) is None


def test_filtro_unidad_negocio_restringe_a_la_propia_un():
    assert filtro_unidad_negocio(_contexto("UN_OPERADOR", 5)) == 5
