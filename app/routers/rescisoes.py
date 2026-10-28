
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.rescisao import MOTIVOS, VERBAS_SUGERIDAS, RescisaoCriar, RescisaoSaida
from app.services import rescisao_service


router = APIRouter(prefix="/rescisoes", tags=["Rescisões"])


@router.get("/motivos")
def motivos():
    return MOTIVOS


@router.get("/verbas-sugeridas")
def verbas_sugeridas():
    return VERBAS_SUGERIDAS


@router.post("", response_model=RescisaoSaida, status_code=201)
def criar(dados: RescisaoCriar, db: Session = Depends(get_db)):
    try:
        return rescisao_service.criar(db, dados)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("", response_model=list[RescisaoSaida])
def listar(db: Session = Depends(get_db)):
    return rescisao_service.listar(db)


@router.get("/{rescisao_id}", response_model=RescisaoSaida)
def detalhar(rescisao_id: int, db: Session = Depends(get_db)):
    try:
        return rescisao_service.obter(db, rescisao_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
