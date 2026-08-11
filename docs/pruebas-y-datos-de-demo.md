# Pruebas y datos de demostración

Cómo verificar que SGAIE funciona de extremo a extremo sin usar datos reales
de CNEL EP. Todo el escenario descrito aquí es **ficticio**: las operadoras,
personas, RUC, cédulas y números de contrato están inventados.

## 1. Suite automatizada del backend

```bash
cd backend
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```

Además de las pruebas por servicio, `tests/test_e2e_flujo_completo.py`
recorre **todas las etapas del negocio en orden**, siempre por HTTP y con
tokens JWT reales:

| Etapa | Qué verifica |
|---|---|
| Catálogo de canon (§6.12) | Alta por SUPERADMIN de los tres tipos de zona |
| Solicitud (§6.7, §9.4) | Numeración `SOL-AAAA-NNNNN` y destinatario según cobertura |
| Checklist documental (§11) | Carga de los 11 documentos, hash SHA-256, rechazo de extensiones no permitidas |
| Workflow (§7.5, §8) | Las cinco etapas, la compuerta documental al 100 %, y el camino observación → subsanación → reenvío |
| Contrato (§7.3) | Nace `EN_JURIDICO`, pasa a `VIGENTE`, y rechaza transiciones inválidas |
| Alquiler anual (§7.2) | Canon calculado desde el desglose por zona |
| Facturación y cobro (§7.4) | Pago parcial → `PARCIAL`, conciliación, pago final → `PAGADA` |
| Morosidad (§6.14) | Días de mora, saldo e interés sobre una factura vencida |
| Novedades (§7.6) | Transiciones `PROGRAMADA→EN_PROCESO→EJECUTADA→CERRADA` y fotografía geolocalizada |
| Alertas y dashboard (§6.14, §7.2) | Alertas de vencimiento, idempotencia del job y consolidado |
| Alcance por rol (§5.2, §5.3) | Matriz solo lectura, aislamiento entre UN, límites del proveedor |

## 2. Base de datos de demostración

```bash
cd backend
.venv/bin/python -m scripts.sembrar_demo
```

Crea `backend/demo_sgaie.db` (SQLite, para no exigir MariaDB en una demo) con
dos Unidades de Negocio, los nueve roles del §2.1, un usuario por rol, dos
operadoras y un expediente completo por cada una: solicitud finalizada,
contrato vigente, alquiler anual con desglose por zona, facturas con pagos,
novedades y las alertas que generan los jobs del §6.14.

El escenario incluye deliberadamente casos "interesantes" para revisar la
interfaz: una operadora al día y otra morosa, una discrepancia entre postes
SIG y físicos, y vencimientos dentro de la ventana de alerta.

Usuarios sembrados — **clave común `Sgaie2026!`**, solo para demostración:

| Usuario | Rol | Alcance |
|---|---|---|
| `admin` | SUPERADMIN | Global |
| `matriz` | MATRIZ_CONSULTA | Global, solo lectura |
| `gye_admin` | UN_ADMIN | CNEL EP Guayaquil |
| `gye_tecnico` | UN_DELEGADO_TECNICO | CNEL EP Guayaquil |
| `gye_gerente` | UN_GERENTE | CNEL EP Guayaquil |
| `gye_juridico` | UN_JURIDICO | CNEL EP Guayaquil |
| `mil_admin` | UN_ADMIN | CNEL EP Milagro |
| `proveedor_teleandes` | PROVEEDOR | TeleAndes Fibra S.A. |
| `proveedor_fibraroja` | PROVEEDOR | FibraRoja Networks Cía. Ltda. |

## 3. Levantar el sistema contra los datos de demo

```bash
# Terminal 1 — backend
cd backend
DATABASE_URL="sqlite:///$(pwd)/demo_sgaie.db" \
CORS_ORIGENES="http://localhost:5173" \
  .venv/bin/python -m uvicorn app.main:app --port 8000

# Terminal 2 — frontend
cd frontend
pnpm install && pnpm dev
```

Abrir <http://localhost:5173> e ingresar con cualquiera de los usuarios de
arriba. Conviene comparar `gye_admin` (ve solo Guayaquil y puede escribir),
`matriz` (ve todo con distintivo de solo lectura) y `proveedor_teleandes`
(ve únicamente su expediente, sin Canon, Alertas ni Usuarios en el menú).

> **Ojo con el nombre de la variable de CORS**: es `CORS_ORIGENES`. El modelo
> de configuración ignora en silencio las variables desconocidas, así que un
> nombre mal escrito deja el valor por defecto de desarrollo y el navegador
> rechaza el login por CORS. `tests/test_config_env_example.py` vigila que
> `.env.example` no se desalinee de los campos reales.

## 4. Componente móvil

El módulo Android se verifica en GitHub Actions (el entorno de desarrollo no
tiene Android SDK ni acceso a `dl.google.com`):

- `.github/workflows/android-apk.yml` ejecuta `testDebugUnitTest` y luego
  `assembleDebug`, publicando el APK como artefacto `sgaie-movil-debug-apk`.
- Las pruebas unitarias corren en JVM, sin emulador, y cubren la lógica pura:
  validaciones del cliente ArcGIS (TLS obligatorio y formato del `GlobalID`),
  el candado de exclusión mutua entre extracción y sincronización, y que el
  estilo del mapa no referencie proveedores remotos de tiles.

Ver `mobile/android/README.md` para instalar el APK en un dispositivo real.
