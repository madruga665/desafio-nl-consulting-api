import pandas as pd
import datetime
from typing import List, Dict, Any, Optional

class AnomalyService:
    def parse_date(self, date_str: Any) -> Optional[datetime.datetime]:
        if not date_str or pd.isna(date_str): return None
        try:
            return datetime.datetime.strptime(str(date_str).strip(), "%d/%m/%Y")
        except:
            return None

    def parse_value(self, value_str: Any) -> float:
        if not value_str or pd.isna(value_str): return 0.0
        try:
            cleaned = str(value_str).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            return float(cleaned)
        except:
            return 0.0

    def _get_clean_name(self, name: Any) -> str:
        return str(name).strip().upper() if not pd.isna(name) else ""

    def validate_nf_duplicates(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        """Regra: NF duplicada no lote."""
        dups_mask = df.duplicated(subset=['NUMERO_DOCUMENTO', '_tmp_fornecedor'], keep=False)
        for _, row in df[dups_mask].iterrows():
            hits.append({
                "arquivo": row['ARQUIVO_ORIGEM'],
                "anomalia": "NF duplicada",
                "slug": "nf_duplicada",
                "criticidade": "Alta",
                "contexto_ia": f"NF {row['NUMERO_DOCUMENTO']} repetida para o fornecedor {row['FORNECEDOR']} neste lote."
            })

    def validate_new_providers(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        """Regra: Fornecedor que aparece apenas uma vez no lote."""
        counts = df['_tmp_fornecedor'].value_counts()
        unicos = counts[counts == 1].index.tolist()
        for _, row in df[df['_tmp_fornecedor'].isin(unicos)].iterrows():
            if row['_tmp_fornecedor']:
                hits.append({
                    "arquivo": row['ARQUIVO_ORIGEM'],
                    "anomalia": "Fornecedor sem histórico",
                    "slug": "fornecedor_novo",
                    "criticidade": "Alta",
                    "contexto_ia": f"O fornecedor '{row['FORNECEDOR']}' é o único deste tipo no lote."
                })

    def validate_new_approvers(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        """Regra: Aprovador que aparece apenas uma vez no lote."""
        counts = df['_tmp_aprovador'].value_counts()
        unicos = counts[counts == 1].index.tolist()
        for _, row in df[df['_tmp_aprovador'].isin(unicos)].iterrows():
            if row['_tmp_aprovador']:
                hits.append({
                    "arquivo": row['ARQUIVO_ORIGEM'],
                    "anomalia": "Aprovador novo",
                    "slug": "aprovador_novo",
                    "criticidade": "Média",
                    "contexto_ia": f"O aprovador '{row['APROVADO_POR']}' aparece apenas uma vez neste lote."
                })

    def validate_divergent_cnpj(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        """Regra: Um fornecedor com múltiplos CNPJs no mesmo lote."""
        cnpj_counts = df.groupby('_tmp_fornecedor')['CNPJ_FORNECEDOR'].nunique()
        divergentes = cnpj_counts[cnpj_counts > 1].index.tolist()
        for _, row in df[df['_tmp_fornecedor'].isin(divergentes)].iterrows():
            hits.append({
                "arquivo": row['ARQUIVO_ORIGEM'],
                "anomalia": "CNPJ divergente",
                "slug": "cnpj_divergente",
                "criticidade": "Alta",
                "contexto_ia": f"O fornecedor {row['FORNECEDOR']} apresenta mais de um CNPJ neste lote."
            })

    def validate_inconsistent_dates(self, row: pd.Series, hits: List[Dict[str, Any]]):
        """Regra: Emissão após o pagamento."""
        dt_emissao = self.parse_date(row.get('DATA_EMISSAO_NF'))
        dt_pagamento = self.parse_date(row.get('DATA_PAGAMENTO'))
        if dt_emissao and dt_pagamento and dt_emissao > dt_pagamento:
            hits.append({
                "arquivo": row['ARQUIVO_ORIGEM'],
                "anomalia": "NF emitida após pagamento",
                "slug": "data_inconsistente",
                "criticidade": "Alta",
                "contexto_ia": f"Emissão {row.get('DATA_EMISSAO_NF')} é posterior ao pagamento {row.get('DATA_PAGAMENTO')}."
            })

    def validate_status_conflict(self, row: pd.Series, hits: List[Dict[str, Any]]):
        """Regra: Cancelado com data de pagamento."""
        status = str(row.get('STATUS', '')).upper()
        if "CANCELADO" in status and row.get('DATA_PAGAMENTO'):
            hits.append({
                "arquivo": row['ARQUIVO_ORIGEM'],
                "anomalia": "STATUS inconsistente",
                "slug": "status_conflitante",
                "criticidade": "Média",
                "contexto_ia": "Documento cancelado mas possui data de pagamento."
            })

    def validate_value_outliers(self, row: pd.Series, stats_df: pd.DataFrame, hits: List[Dict[str, Any]]):
        """Regra: Valor muito acima da média do fornecedor no lote."""
        f_key = row['_tmp_fornecedor']
        if f_key in stats_df.index:
            stats = stats_df.loc[f_key]
            mean_val = float(stats['mean']) # type: ignore
            count_val = int(stats['count']) # type: ignore
            val_atual = float(row['_tmp_val_numeric']) # type: ignore
            
            if count_val >= 3 and val_atual > (mean_val * 2.5):
                hits.append({
                    "arquivo": row['ARQUIVO_ORIGEM'],
                    "anomalia": "Valor fora da faixa do fornecedor",
                    "slug": "outlier_valor",
                    "criticidade": "Média",
                    "contexto_ia": f"Valor R$ {val_atual} muito acima da média do lote (R$ {mean_val:.2f})."
                })

    def validate_parsing_errors(self, row: pd.Series, hits: List[Dict[str, Any]]):
        """Regra: Campos essenciais faltando ou truncados."""
        if not row.get('NUMERO_DOCUMENTO') or not row.get('FORNECEDOR'):
            hits.append({
                "arquivo": row['ARQUIVO_ORIGEM'],
                "anomalia": "Arquivo não processável",
                "slug": "erro_parsing",
                "criticidade": "Média",
                "contexto_ia": "Dados essenciais ausentes."
            })

    async def run_programmatic_audit(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Orquestra as validações separadas e limpa colunas temporárias."""
        hits = []
        
        # Criar colunas temporárias para cálculo
        df['_tmp_fornecedor'] = df['FORNECEDOR'].apply(self._get_clean_name)
        df['_tmp_aprovador'] = df['APROVADO_POR'].apply(self._get_clean_name)
        df['_tmp_val_numeric'] = df['VALOR_BRUTO'].apply(self.parse_value)
        stats_por_fornecedor = df.groupby('_tmp_fornecedor')['_tmp_val_numeric'].agg(['mean', 'count'])

        # Validações de Conjunto (DataFrame)
        self.validate_nf_duplicates(df, hits)
        self.validate_new_providers(df, hits)
        self.validate_new_approvers(df, hits)
        self.validate_divergent_cnpj(df, hits)

        # Validações Linha a Linha
        for _, row in df.iterrows():
            self.validate_inconsistent_dates(row, hits)
            self.validate_status_conflict(row, hits)
            self.validate_parsing_errors(row, hits)
            self.validate_value_outliers(row, stats_por_fornecedor, hits)

        # LIMPEZA
        df.drop(columns=['_tmp_fornecedor', '_tmp_aprovador', '_tmp_val_numeric'], inplace=True)
        
        return hits

anomaly_service = AnomalyService()
