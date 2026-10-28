import hashlib
import json
import shutil
from pathlib import Path

from fastapi import HTTPException

from app.core.paths import GENERATED_DIR, TEMPLATES_DIR
from app.services.pdf_service import gerar_preview_recibo


class DocumentService:
    TEMPLATES = {
        "recibo": TEMPLATES_DIR / "recibo_pagamento.xlsx",
        "rescisao": TEMPLATES_DIR / "rescisao_por_fora.xlsx",
    }

    def gerar_anexo(self, colaborador: dict, tipo_documento: str) -> dict | None:
        template = self.TEMPLATES.get(tipo_documento, self.TEMPLATES["recibo"])
        if not template.exists():
            return None
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        nome_seguro = "".join(char if char.isalnum() else "_" for char in colaborador["nome"])
        versao = hashlib.sha1(json.dumps({**colaborador, "tipo": tipo_documento}, sort_keys=True).encode()).hexdigest()[:8]
        prefixo = "rescisao" if tipo_documento == "rescisao" else "recibo"
        xlsx = GENERATED_DIR / f"{prefixo}_{nome_seguro}_{versao}.xlsx"
        pdf = GENERATED_DIR / f"{tipo_documento}_{nome_seguro}_{versao}.pdf"
        if not xlsx.exists() or not pdf.exists():
            shutil.copyfile(template, xlsx)
            self._preencher_xlsx(xlsx, colaborador, tipo_documento)
            gerar_preview_recibo(colaborador["nome"], colaborador["email"], colaborador["cargo"], colaborador["salario"], pdf)
        return {"nome": xlsx.name, "caminho": str(xlsx), "tipo": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "preview_pdf": pdf.name, "tipo_documento": tipo_documento}

    def _preencher_xlsx(self, caminho: Path, colaborador: dict, tipo_documento: str) -> None:
        try:
            from openpyxl import load_workbook
        except ImportError as error:
            raise HTTPException(503, "Dependência openpyxl ausente. Execute: python -m pip install openpyxl") from error
        workbook = load_workbook(caminho)
        sheet = workbook.active
        if tipo_documento == "recibo":
            sheet["C11"] = colaborador["nome"]
            sheet["I11"] = colaborador["cargo"]
            sheet["I15"] = colaborador["salario"]
        else:
            sheet["D5"] = colaborador["nome"]
            sheet["D15"] = colaborador["nome"]
            sheet["B28"] = colaborador["salario"]
        workbook.save(caminho)
