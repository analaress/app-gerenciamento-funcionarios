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
    SugestaoEntrada,
    SugestaoSaida,
)
from app.services import rescisao_service

router = APIRouter(prefix="/rescisoes", tags=["Rescisões"])


class EnviarEmailEntrada(BaseModel):
    # se vier vazio, usa o e-mail cadastrado do colaborador
    destinatario: str | None = None


@router.get("/motivos")
def motivos():
    return MOTIVOS


@router.get("/verbas-sugeridas")
def verbas_sugeridas():
    return VERBAS_SUGERIDAS


@router.get("/email-modo")
def email_modo():
    """Diz à tela se o e-mail está em modo de teste (grava um arquivo em vez de enviar)."""
    return {"simulado": rescisao_service.email_em_modo_de_teste()}


@router.post("/sugestao", response_model=SugestaoSaida)
def sugerir(dados: SugestaoEntrada, db: Session = Depends(get_db)):
    """Sugere valores para as verbas (saldo de salário, 13º, férias e FGTS). A pessoa confere e edita."""
    try:
        return rescisao_service.sugerir(db, dados)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("", response_model=RescisaoSaida, status_code=201)
def criar(dados: RescisaoCriar, db: Session = Depends(get_db)):
    try:
        return rescisao_service.criar(db, dados)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
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


@router.put("/{rescisao_id}", response_model=RescisaoSaida)
def corrigir(rescisao_id: int, dados: RescisaoCriar, db: Session = Depends(get_db)):
    """Correção manual dos dados (também depois de gerada: volta para EM_CONFERENCIA)."""
    try:
        return rescisao_service.corrigir(db, rescisao_id, dados)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.post("/{rescisao_id}/gerar", response_model=RescisaoSaida)
def gerar(rescisao_id: int, db: Session = Depends(get_db)):
    """Gera o PDF e muda o status para GERADO."""
    try:
        return rescisao_service.gerar_pdf(db, rescisao_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except RuntimeError as erro:
        raise HTTPException(status_code=500, detail=str(erro))


@router.get("/{rescisao_id}/pdf")
def baixar_pdf(rescisao_id: int, db: Session = Depends(get_db)):
    """Baixa o PDF já gerado."""
    try:
        caminho = rescisao_service.caminho_do_pdf(db, rescisao_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except FileNotFoundError as erro:
        raise HTTPException(status_code=409, detail=str(erro))
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
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
    except FileNotFoundError as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except RuntimeError as erro:
        raise HTTPException(status_code=502, detail=str(erro))


@router.get("/{rescisao_id}/envios", response_model=list[EnvioSaida])
def listar_envios(rescisao_id: int, db: Session = Depends(get_db)):
    """Histórico de tentativas de envio (data, destinatário, sucesso/erro)."""
    try:
        return rescisao_service.listar_envios(db, rescisao_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
