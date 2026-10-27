from fastapi import FastAPI
from app.core.database import Base, engine
# from app.models import historico_documento  
from app.models import empresa
# from app.routers import historico            
from app.routers import empresas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gerenciamento de Funcionários")

# app.include_router(historico.router)         
app.include_router(empresas.router)
