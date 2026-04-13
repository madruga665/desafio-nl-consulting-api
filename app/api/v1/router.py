from fastapi import APIRouter
from app.api.v1.endpoints import documents

api_router = APIRouter()

# Rota de processamento de documentos
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Exemplo de rota de teste (Health Check)
@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
