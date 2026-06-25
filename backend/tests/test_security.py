"""Pruebas de primitivas de seguridad (§4): hashing, JWT y cifrado AES-256-GCM."""

from datetime import datetime, timezone

import jwt
import pytest

from app.core.security import (
    cifrar_valor,
    crear_token_acceso,
    crear_token_refresco,
    decodificar_token,
    descifrar_valor,
    hashear_password,
    verificar_password,
)


def test_hashear_password_no_almacena_texto_plano():
    hash_resultante = hashear_password("Clave123!")
    assert hash_resultante != "Clave123!"
    assert verificar_password("Clave123!", hash_resultante)


def test_verificar_password_rechaza_clave_incorrecta():
    hash_resultante = hashear_password("Clave123!")
    assert not verificar_password("OtraClave!", hash_resultante)


def test_token_acceso_codifica_claims_esperados():
    token = crear_token_acceso(
        usuario_id=1,
        username="admin",
        rol="SUPERADMIN",
        unidad_negocio_id=None,
        tipo_cuenta="LOCAL",
    )
    payload = decodificar_token(token)
    assert payload["sub"] == "1"
    assert payload["username"] == "admin"
    assert payload["rol"] == "SUPERADMIN"
    assert payload["unidad_negocio_id"] is None
    assert payload["tipo_token"] == "acceso"


def test_token_refresco_incluye_jti_para_revocacion():
    token, jti, expiracion = crear_token_refresco(usuario_id=7)
    payload = decodificar_token(token)
    assert payload["jti"] == jti
    assert payload["tipo_token"] == "refresco"
    assert payload["sub"] == "7"
    assert expiracion > datetime.now(timezone.utc)


def test_decodificar_token_invalido_lanza_pyjwt_error():
    with pytest.raises(jwt.PyJWTError):
        decodificar_token("token-no-valido")


def test_cifrar_y_descifrar_valor_es_reversible():
    original = "1234567890"
    cifrado = cifrar_valor(original)
    assert cifrado != original
    assert descifrar_valor(cifrado) == original


def test_cifrar_valor_produce_salidas_distintas_por_nonce_aleatorio():
    cifrado_1 = cifrar_valor("mismo-valor")
    cifrado_2 = cifrar_valor("mismo-valor")
    assert cifrado_1 != cifrado_2
