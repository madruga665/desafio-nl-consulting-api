from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document
from app.models.history import Provider, Approver

class DocumentRepository:
    async def save_batch_data(self, db: AsyncSession, documents_data: List[Dict[str, Any]]):
        """
        Popula as tabelas documents, providers e approvers mantendo os relacionamentos.
        """
        for data in documents_data:
            # 1. Resolver/Criar Provider
            current_provider_id: Optional[int] = None
            if data.get("FORNECEDOR"):
                res_p = await db.execute(select(Provider).where(Provider.nome == data["FORNECEDOR"]))
                provider = res_p.scalars().first()
                
                val = float(data.get("valor_bruto_float", 0.0))
                if not provider:
                    provider = Provider(
                        nome=data["FORNECEDOR"],
                        cnpj_padrao=data.get("CNPJ_FORNECEDOR"),
                        valor_medio=val,
                        total_documentos=1
                    )
                    db.add(provider)
                    await db.flush()
                else:
                    # Atualiza média móvel e total usando tipos nativos
                    old_total = provider.total_documentos
                    new_total = old_total + 1
                    provider.valor_medio = (provider.valor_medio * old_total + val) / new_total
                    provider.total_documentos = new_total
                    
                    if not provider.cnpj_padrao:
                        provider.cnpj_padrao = data.get("CNPJ_FORNECEDOR")
                
                current_provider_id = provider.id

            # 2. Resolver/Criar Approver
            current_approver_id: Optional[int] = None
            if data.get("APROVADO_POR"):
                res_a = await db.execute(select(Approver).where(Approver.nome == data["APROVADO_POR"]))
                approver = res_a.scalars().first()
                if not approver:
                    approver = Approver(nome=data["APROVADO_POR"], ativo=1)
                    db.add(approver)
                    await db.flush()
                
                current_approver_id = approver.id

            # 3. Salvar o Documento vinculado aos relacionamentos
            new_doc = Document(
                arquivo_origem=data.get("ARQUIVO_ORIGEM", "desconhecido"),
                tipo_documento=data.get("TIPO_DOCUMENTO"),
                numero_documento=data.get("NUMERO_DOCUMENTO"),
                valor_bruto=float(data.get("valor_bruto_float", 0.0)),
                status=data.get("STATUS"),
                provider_id=current_provider_id,
                approver_id=current_approver_id
            )
            db.add(new_doc)

        await db.commit()

document_repository = DocumentRepository()
