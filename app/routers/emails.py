from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import colaborador_repository, email_repository
from app.schemas.email import EmailCreate

router = APIRouter(prefix="/emails", tags=["emails"])

@router.get("")
def listar():
    return email_repository.listar_todos()


@router.post("/colaborador/{colaborador_id}")
def enviar(colaborador_id: int, data: EmailCreate, db: Session = Depends(get_db)):
    colaborador = colaborador_repository.buscar_por_id(db, colaborador_id)
    if colaborador is None:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")

    return email_repository.registrar(
        documento_id=colaborador_id,
        destinatario=colaborador.email,
        status="ENVIADO",
        simulado=True,
    )
