from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentData(BaseModel):
    """Modelo para representar os campos de um documento .txt extraído."""
    TIPO_DOCUMENTO: Optional[str] = None
    NUMERO_DOCUMENTO: Optional[str] = None
    DATA_EMISSAO: Optional[str] = None
    FORNECEDOR: Optional[str] = None
    CNPJ_FORNECEDOR: Optional[str] = None
    DESCRICAO_SERVICO: Optional[str] = None
    VALOR_BRUTO: Optional[str] = None
    DATA_PAGAMENTO: Optional[str] = None
    DATA_EMISSAO_NF: Optional[str] = None
    APROVADO_POR: Optional[str] = None
    BANCO_DESTINO: Optional[str] = None
    STATUS: Optional[str] = None
    HASH_VERIFICACAO: Optional[str] = None
    
    # Campos extras para categorização e anomalias
    ARQUIVO_ORIGEM: str
    ENCODING_DETECTADO: str
    ANOMALIAS: List[str] = Field(default_factory=list)
    CATEGORIA: str = "NORMAL" # NORMAL, ANOMALIA, ERRO_LEITURA
    IA_ANALISE: Optional[str] = None # Resultado da análise do Gemini

