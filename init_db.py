import asyncio
from app.core.database import engine, Base
from app.models.document import Document
from app.models.history import Provider, Approver

async def init_db():
    async with engine.begin() as conn:
        # Cria as tabelas se não existirem
        await conn.run_sync(Base.metadata.create_all)
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    asyncio.run(init_db())
