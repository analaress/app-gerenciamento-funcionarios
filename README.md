# Gerenciamento de Funcionários

Projeto FastAPI organizado por camadas para o MVP de empresas, colaboradores, recibos, rescisões, documentos, e-mails e histórico.

## Requisitos

- Python 3.11 ou superior
- PowerShell ou outro terminal compatível

## Criar o ambiente virtual

No Windows PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute uma vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois, ative novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Instalar dependências

Com o ambiente virtual ativado:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configurar ambiente

Copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Preencha as variáveis do arquivo `.env` quando os recursos de banco de dados e envio de e-mail forem implementados.

## Rodar o projeto

Com o ambiente virtual ativado:

```powershell
python -m uvicorn app.main:app --reload
```

A API ficará disponível em:

- http://127.0.0.1:8000
- Documentação Swagger: http://127.0.0.1:8000/docs
- Documentação ReDoc: http://127.0.0.1:8000/redoc

## Comandos rápidos

```powershell
cd C:\Users\User\ponto-agil\gerenciamento-funcionarios
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Para desativar o ambiente virtual:

```powershell
deactivate
```

Consulte [docs/api.md](docs/api.md) para a documentação dos endpoints.

## Estrutura

O fluxo planejado é:

```text
routers → services → repositories → models
```

Os `schemas` definem os contratos de entrada e saída da API.
## Teste de e-mail local

O envio padrão é mockado e grava o resultado em `app/data/emails_enviados.json`.

Para visualizar mensagens localmente sem Docker, use o servidor SMTP embutido:

Defina no ambiente:

```powershell
$env:EMAIL_PROVIDER="local"
$env:SMTP_HOST="127.0.0.1"
$env:SMTP_PORT="2525"
$env:EMAIL_FROM="sistema@localhost"
```

Inicie a API e envie pelo formulário em `/ui/emails/novo`. A caixa de entrada local fica em `http://127.0.0.1:8000/ui/inbox` e o recibo XLSX é anexado automaticamente.

O PDF é um preview simplificado dos dados principais do documento. O XLSX original preenchido continua sendo o anexo oficial.
