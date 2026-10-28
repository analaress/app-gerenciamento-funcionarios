from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.rescisao import (
    MOTIVOS,
    VERBAS_SUGERIDAS,
    EnvioSaida,
    RescisaoCriar,
    RescisaoSaida,
)
from app.services import rescisao_service

router = APIRouter(prefix="/rescisoes", tags=["Rescisões"])


class EnviarEmailEntrada(BaseModel):
    # se vier vazio, usa o e-mail cadastrado do colaborador
    destinatario: str | None = None


@router.get("/motivos")
def listar_motivos():
    return MOTIVOS


@router.get("/verbas-sugeridas")
def listar_verbas_sugeridas():
    return VERBAS_SUGERIDAS


@router.post("/", response_model=RescisaoSaida, status_code=201)
def criar(dados: RescisaoCriar, db: Session = Depends(get_db)):
    try:
        return rescisao_service.criar_rescisao(db, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[RescisaoSaida])
def listar(db: Session = Depends(get_db)):
    return rescisao_service.listar_rescisoes(db)


@router.get("/{rescisao_id}", response_model=RescisaoSaida)
def detalhar(rescisao_id: int, db: Session = Depends(get_db)):
    try:
        return rescisao_service.obter_rescisao(db, rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{rescisao_id}", response_model=RescisaoSaida)
def corrigir(rescisao_id: int, dados: RescisaoCriar, db: Session = Depends(get_db)):
    """Correção manual dos dados (também depois de gerada: volta para EM_CONFERENCIA)."""
    try:
        return rescisao_service.corrigir_rescisao(db, rescisao_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rescisao_id}/gerar", response_model=RescisaoSaida)
def gerar(rescisao_id: int, db: Session = Depends(get_db)):
    """Gera o PDF e muda o status para GERADO."""
    try:
        return rescisao_service.gerar_pdf(db, rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rescisao_id}/pdf")
def baixar_pdf(rescisao_id: int, db: Session = Depends(get_db)):
    """Baixa o PDF já gerado."""
    try:
        caminho = rescisao_service.caminho_do_pdf(db, rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=f"rescisao_{rescisao_id}.pdf",
    )


@router.post("/{rescisao_id}/enviar", response_model=RescisaoSaida)
def enviar(
    rescisao_id: int,
    dados: EnviarEmailEntrada | None = None,
    db: Session = Depends(get_db),
):
    """Envia o PDF por e-mail. Status vira ENVIADO (sucesso) ou ERRO_ENVIO (falha)."""
    try:
        return rescisao_service.enviar_email(db, rescisao_id, dados.destinatario if dados else None)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{rescisao_id}/envios", response_model=list[EnvioSaida])
def listar_envios(rescisao_id: int, db: Session = Depends(get_db)):
    """Histórico de tentativas de envio (data, destinatário, sucesso/erro)."""
    try:
        return rescisao_service.listar_envios(db, rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
