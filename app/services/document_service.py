import zipfile
import io
import chardet
import pandas as pd
import datetime
from typing import List, Dict, Any, Optional
from app.services.ai_service import gemini_service
from app.services.anomaly_service import anomaly_service
from app.repositories.document_repository import document_repository
from app.core.database import AsyncSessionLocal

class DocumentService:
    @staticmethod
    def detect_encoding(content: bytes) -> str:
        result = chardet.detect(content)
        return result.get('encoding', 'utf-8') or 'utf-8'

    async def process_zip_file(self, zip_content: bytes) -> bytes:
        documents_raw = []
        keys_to_ignore = {"DATA_EMISSAO", "ANOMALIAS_SLUGS", "OBSERVACAO"}

        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            for filename in z.namelist():
                if filename.endswith('.txt'):
                    with z.open(filename) as f:
                        raw = f.read()
                        encoding = self.detect_encoding(raw)
                        try: content = raw.decode(encoding)
                        except: content = raw.decode('latin-1', errors='replace')
                        
                        data: Dict[str, Any] = {"ARQUIVO_ORIGEM": filename, "ENCODING": encoding}
                        for line in content.splitlines():
                            if ":" in line:
                                k, v = line.split(":", 1)
                                key = k.strip()
                                if key not in keys_to_ignore: data[key] = v.strip()
                        
                        data["valor_bruto_float"] = anomaly_service.parse_value(data.get("VALOR_BRUTO"))
                        documents_raw.append(data)

        if not documents_raw: raise ValueError("Nenhum .txt encontrado.")
        df_final = pd.DataFrame(documents_raw)
        
        async with AsyncSessionLocal() as db:
            # 1. Auditoria Programática
            found_hits = await anomaly_service.run_programmatic_audit(df_final)
            
            # 2. Enriquecimento pela IA (Limitado a 100 por segurança)
            enriched_hits, tokens = await gemini_service.enrich_anomalies_table(found_hits[:100])
            
            # 3. Persistência
            # await document_repository.save_batch_data(db, documents_raw)

        # 4. Preparar Excel
        df_anomalias = pd.DataFrame(enriched_hits)
        
        # Garantia de colunas
        for col in ['explicacao', 'recomendacao']:
            if col not in df_anomalias.columns:
                df_anomalias[col] = ""

        if not df_anomalias.empty:
            # Definimos a ordem das colunas aqui (Explicação e Recomendação por último)
            column_mapping = {
                'arquivo': 'Arquivo Analisado', 
                'anomalia': 'Anomalia Detectada',
                'criticidade': 'Nível de Criticidade', 
                'slug': 'Slug da Regra',
                'explicacao': 'Explicação',
                'recomendacao': 'Recomendação'
            }
            # Renomear
            df_anomalias = df_anomalias.rename(columns=column_mapping)
            # Aplicar a ordem baseada no dicionário acima
            cols_excel = [c for c in column_mapping.values() if c in df_anomalias.columns]
            df_anomalias = df_anomalias[cols_excel]

        df_metadata = pd.DataFrame([{
            "Timestamp Processamento": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Status IA": tokens.get("status", "failed"),
            "Erro IA": tokens.get("error", "Nenhum"),
            "Prompt Version": gemini_service.PROMPT_VERSION,
            "Total Arquivos": len(df_final),
            "Tokens Entrada": tokens.get("prompt_tokens", 0),
            "Tokens Saída": tokens.get("candidates_tokens", 0)
        }])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.drop(columns=["valor_bruto_float", "val_numeric"], errors='ignore').to_excel(writer, index=False, sheet_name='Documentos Extraídos')
            df_anomalias.to_excel(writer, index=False, sheet_name='Anomalias')
            df_metadata.to_excel(writer, index=False, sheet_name='Metadados Auditoria')
            
        return output.getvalue()

document_service = DocumentService()
