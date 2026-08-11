"""El .env.example debe corresponder con los campos reales de Configuracion.

`Configuracion` usa `extra="ignore"`, así que una variable mal escrita en el
archivo de ejemplo no falla: se ignora en silencio y el valor por defecto queda
en producción. Fue exactamente lo que pasó con `CORS_ORIGENS` (el campo es
`cors_origenes`), que dejaba la lista de orígenes CORS del §4.5 en su valor de
desarrollo por más que el operador la configurara siguiendo la documentación.
"""

from pathlib import Path

from app.core.config import Configuracion

RUTA_ENV_EJEMPLO = Path(__file__).resolve().parent.parent / ".env.example"


def _variables_documentadas() -> set[str]:
    variables = set()
    for linea in RUTA_ENV_EJEMPLO.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        variables.add(linea.split("=", 1)[0].strip())
    return variables


def test_toda_variable_del_env_example_existe_en_la_configuracion():
    campos = {nombre.upper() for nombre in Configuracion.model_fields}
    desconocidas = _variables_documentadas() - campos
    assert not desconocidas, (
        "Variables en .env.example que Configuracion ignoraría silenciosamente: "
        f"{sorted(desconocidas)}"
    )


def test_el_env_example_documenta_los_ajustes_criticos_de_seguridad():
    """Los parámetros sin default seguro deben estar sí o sí en el ejemplo (§4)."""
    documentadas = _variables_documentadas()
    for critica in ("DATABASE_URL", "JWT_SECRET_KEY", "AES_MASTER_KEY", "CORS_ORIGENES"):
        assert critica in documentadas, f"Falta {critica} en .env.example"
