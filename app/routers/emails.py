from fastapi import APIRouter
from app.schemas.email import EmailCreate
from app.services.email_service import EmailService

router = APIRouter(prefix="/emails", tags=["emails"])
service = EmailService()

@router.get("")
def listar(): return service.listar()
@router.post("/colaborador/{colaborador_id}")
def enviar(colaborador_id: int, data: EmailCreate): return service.enviar_para_colaborador(colaborador_id, data)
