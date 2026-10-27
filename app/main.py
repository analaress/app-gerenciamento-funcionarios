from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
# from app.models import historico_documento  
from app.models import empresa
# from app.routers import historico            
from app.routers import empresas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gerenciamento de Funcionários")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(historico.router)         
app.include_router(empresas.router)
