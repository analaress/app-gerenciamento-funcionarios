from dataclasses import dataclass


@dataclass
class Empresa:
    id: int
    razao_social: str      # campo 02 do TRCT
    cnpj: str              # campo 01
    email: str
    logradouro: str        # campo 03
    bairro: str            # campo 04
    municipio: str         # campo 05
    uf: str                # campo 06
    cep: str               # campo 07
    cnae: str              # campo 08
