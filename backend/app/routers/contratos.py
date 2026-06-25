"""Endpoints de Contrato (§6.5, §7.1, §10), con alcance por UN (§5.2) y
transiciones de estado controladas (validadas en el servicio)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import UsuarioContexto, obtener_usuario_actual, requerir_escritura
from app.db.session import obtener_db
from app.schemas.contrato import ContratoActualizar, ContratoCrear, ContratoRespuesta
from app.services import contrato as servicio

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.get("", response_model=list[ContratoRespuesta])
def listar(
    db: Session = Depends(obtener_db), usuario: UsuarioContexto = Depends(obtener_usuario_actual)
):
    return servicio.listar(db, usuario)


@router.get("/{contrato_id}", response_model=ContratoRespuesta)
def obtener(
    contrato_id: int,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(obtener_usuario_actual),
):
    return servicio.obtener(db, contrato_id, usuario)


@router.post("", response_model=ContratoRespuesta, status_code=201)
def crear(
    datos: ContratoCrear,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.crear(db, datos, usuario)


@router.put("/{contrato_id}", response_model=ContratoRespuesta)
def actualizar(
    contrato_id: int,
    datos: ContratoActualizar,
    db: Session = Depends(obtener_db),
    usuario: UsuarioContexto = Depends(requerir_escritura),
):
    return servicio.actualizar(db, contrato_id, datos, usuario)
