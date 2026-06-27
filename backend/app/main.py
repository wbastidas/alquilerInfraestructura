"""Punto de entrada de la API SGAIE (FastAPI). Cablea middlewares de seguridad
transversales (§4) y los routers de la superficie de API (§10)."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import obtener_configuracion
from app.core.exceptions import (
    PermisoDenegado,
    RecursoDuplicado,
    RecursoNoEncontrado,
    TransicionInvalida,
)
from app.jobs.scheduler import crear_scheduler
from app.middlewares.rate_limit import limiter
from app.middlewares.security_headers import CabecerasSeguridadMiddleware
from app.routers import alquileres_anuales as alquileres_anuales_router
from app.routers import auth as auth_router
from app.routers import catalogo_canon as catalogo_canon_router
from app.routers import contratos as contratos_router
from app.routers import documentos as documentos_router
from app.routers import novedades as novedades_router
from app.routers import operadoras as operadoras_router
from app.routers import pagos as pagos_router
from app.routers import solicitudes as solicitudes_router
from app.routers import unidades_negocio as unidades_negocio_router
from app.routers import usuarios as usuarios_router

config = obtener_configuracion()

app = FastAPI(
    title="SGAIE - Sistema de Gestión de Arriendo de Infraestructura Eléctrica",
    description="API del sistema de arrendamiento de postes/ductos de CNEL EP a operadoras de telecomunicaciones.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Traducción de excepciones de dominio a respuestas HTTP, común a todos los routers
# (el filtro de alcance por UN del §5.2 vive en los servicios, no en cada endpoint).
@app.exception_handler(RecursoNoEncontrado)
def _manejar_no_encontrado(request: Request, exc: RecursoNoEncontrado) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PermisoDenegado)
def _manejar_permiso_denegado(request: Request, exc: PermisoDenegado) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(TransicionInvalida)
def _manejar_transicion_invalida(request: Request, exc: TransicionInvalida) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(RecursoDuplicado)
def _manejar_recurso_duplicado(request: Request, exc: RecursoDuplicado) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValueError)
def _manejar_value_error(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.add_middleware(CabecerasSeguridadMiddleware)

# CORS restrictivo: orígenes explícitos por entorno, nunca "*" en producción (§4.5).
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.lista_cors_origenes,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

PREFIJO_API = "/api/v1"
app.include_router(auth_router.router, prefix=PREFIJO_API)
app.include_router(unidades_negocio_router.router, prefix=PREFIJO_API)
app.include_router(usuarios_router.router, prefix=PREFIJO_API)
app.include_router(operadoras_router.router, prefix=PREFIJO_API)
app.include_router(contratos_router.router, prefix=PREFIJO_API)
app.include_router(catalogo_canon_router.router, prefix=PREFIJO_API)
app.include_router(alquileres_anuales_router.router, prefix=PREFIJO_API)
app.include_router(solicitudes_router.router, prefix=PREFIJO_API)
app.include_router(documentos_router.router, prefix=PREFIJO_API)
app.include_router(pagos_router.router, prefix=PREFIJO_API)
app.include_router(novedades_router.router, prefix=PREFIJO_API)


@app.get("/api/v1/salud", tags=["salud"])
def salud() -> dict[str, str]:
    return {"estado": "ok"}


# Job de auto-generación anual (§7.2): un BackgroundScheduler en proceso, con
# fallback documentado a Programador de tareas de Windows (§3.3) si el backend
# no corre 24/7.
@app.on_event("startup")
def _iniciar_scheduler() -> None:
    app.state.scheduler = crear_scheduler()
    app.state.scheduler.start()


@app.on_event("shutdown")
def _detener_scheduler() -> None:
    app.state.scheduler.shutdown(wait=False)
