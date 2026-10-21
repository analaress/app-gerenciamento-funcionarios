from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.rescisao import MOTIVOS, VERBAS_SUGERIDAS, RescisaoCriar, RescisaoSaida
from app.services import rescisao_service

router = APIRouter(prefix="/rescisoes", tags=["Rescisões"])


@router.get("/motivos")
def listar_motivos():
    return MOTIVOS


@router.get("/verbas-sugeridas")
def listar_verbas_sugeridas():
    return VERBAS_SUGERIDAS


@router.post("/", response_model=RescisaoSaida, status_code=201)
def criar(dados: RescisaoCriar):
    try:
        return rescisao_service.criar_rescisao(dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[RescisaoSaida])
def listar():
    return rescisao_service.listar_rescisoes()


@router.get("/{rescisao_id}", response_model=RescisaoSaida)
def detalhar(rescisao_id: int):
    try:
        return rescisao_service.obter_rescisao(rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{rescisao_id}", response_model=RescisaoSaida)
def corrigir(rescisao_id: int, dados: RescisaoCriar):
    try:
        return rescisao_service.corrigir_rescisao(rescisao_id, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rescisao_id}/gerar", response_model=RescisaoSaida)
def gerar(rescisao_id: int):
    """Gera o PDF e muda o status para GERADO."""
    try:
        return rescisao_service.gerar_pdf(rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rescisao_id}/pdf")
def baixar_pdf(rescisao_id: int):
    """Baixa o PDF já gerado."""
    try:
        caminho = rescisao_service.caminho_do_pdf(rescisao_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=f"rescisao_{rescisao_id}.pdf",
    )
