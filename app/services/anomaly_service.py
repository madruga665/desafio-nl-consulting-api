import pandas as pd
import datetime
import re
from typing import List, Dict, Any, Optional


class AnomalyService:
    def parse_date(self, date_str: Any) -> Optional[datetime.datetime]:
        if not date_str or pd.isna(date_str):
            return None
        try:
            return datetime.datetime.strptime(str(date_str).strip(), "%d/%m/%Y")
        except:
            return None

    def parse_value(self, value_str: Any) -> float:
        if not value_str or pd.isna(value_str):
            return 0.0
        try:
            val_clean = str(value_str).replace("R$", "").replace(" ", "")
            if "," in val_clean and "." in val_clean:
                val_clean = val_clean.replace(".", "").replace(",", ".")
            elif "," in val_clean:
                val_clean = val_clean.replace(",", ".")
            return float(val_clean)
        except:
            return 0.0

    def _get_clean_name(self, name: Any) -> str:
        return str(name).strip().upper() if not pd.isna(name) else ""

    def validate_nf_duplicates(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        dups_mask = df.duplicated(
            subset=["NUMERO_DOCUMENTO", "_tmp_fornecedor"], keep=False
        )
        for _, row in df[dups_mask].iterrows():
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "NF duplicada",
                    "slug": "nf_duplicada",
                    "criticidade": "Alta",
                    "contexto_ia": f"NF {row['NUMERO_DOCUMENTO']} repetida para o fornecedor {row['FORNECEDOR']}.",
                }
            )

    def validate_new_providers(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        counts = df["_tmp_fornecedor"].value_counts()
        unicos = counts[counts == 1].index.tolist()
        for _, row in df[df["_tmp_fornecedor"].isin(unicos)].iterrows():
            if row["_tmp_fornecedor"]:
                hits.append(
                    {
                        "arquivo": row["ARQUIVO_ORIGEM"],
                        "anomalia": "Fornecedor sem histórico",
                        "slug": "fornecedor_novo",
                        "criticidade": "Alta",
                        "contexto_ia": f"Fornecedor '{row['FORNECEDOR']}' aparece apenas uma vez no lote.",
                    }
                )

    def validate_new_approvers(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        counts = df["_tmp_aprovador"].value_counts()
        unicos = counts[counts == 1].index.tolist()
        for _, row in df[df["_tmp_aprovador"].isin(unicos)].iterrows():
            if row["_tmp_aprovador"]:
                hits.append(
                    {
                        "arquivo": row["ARQUIVO_ORIGEM"],
                        "anomalia": "Aprovador novo",
                        "slug": "aprovador_novo",
                        "criticidade": "Média",
                        "contexto_ia": f"Aprovador '{row['APROVADO_POR']}' aparece apenas uma vez no lote.",
                    }
                )

    def validate_numeric_value(self, row: pd.Series, hits: List[Dict[str, Any]]):
        raw_val = row.get("VALOR_BRUTO")
        if not raw_val or pd.isna(raw_val) or str(raw_val).strip() == "":
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Valor bruto inválido",
                    "slug": "valor_invalido",
                    "criticidade": "Alta",
                    "contexto_ia": "Campo VALOR_BRUTO vazio.",
                }
            )
            return
        if not re.search(r"\d", str(raw_val)):
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Valor bruto inválido",
                    "slug": "valor_invalido",
                    "criticidade": "Alta",
                    "contexto_ia": f"Valor '{raw_val}' sem dígitos.",
                }
            )
            return
        val_num = self.parse_value(raw_val)
        if val_num <= 0:
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Valor bruto inválido",
                    "slug": "valor_invalido",
                    "criticidade": "Alta",
                    "contexto_ia": f"Valor extraído: {val_num}",
                }
            )

    def validate_hash_format(self, row: pd.Series, hits: List[Dict[str, Any]]):
        """Regra: Valida padrão de Hash (3 letras + 10 números)."""
        h_val = str(row.get("HASH_VERIFICACAO", "")).strip()
        # Regex: 3 letras (A-Z) seguidas de 10 dígitos (0-9)
        if not re.fullmatch(r"[A-Z]{3}\d{10}", h_val):
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Hash inválido",
                    "slug": "hash_invalido",
                    "criticidade": "Alta",
                    "contexto_ia": f"O hash '{h_val}' não segue o padrão esperado (3 letras + 10 números).",
                }
            )

    def validate_divergent_cnpj(self, df: pd.DataFrame, hits: List[Dict[str, Any]]):
        counts = (
            df.groupby(["_tmp_fornecedor", "CNPJ_FORNECEDOR"])
            .size()
            .reset_index(name="qtd")
        )
        for fornecedor in counts["_tmp_fornecedor"].unique():
            if not fornecedor:
                continue
            subset = counts[counts["_tmp_fornecedor"] == fornecedor]
            if len(subset) > 1:
                id_max = subset["qtd"].idxmax()
                cnpj_padrao = subset.loc[id_max, "CNPJ_FORNECEDOR"]
                anomalos = df[
                    (df["_tmp_fornecedor"] == fornecedor)
                    & (df["CNPJ_FORNECEDOR"] != cnpj_padrao)
                ]
                for _, row in anomalos.iterrows():
                    hits.append(
                        {
                            "arquivo": row["ARQUIVO_ORIGEM"],
                            "anomalia": "CNPJ divergente",
                            "slug": "cnpj_divergente",
                            "criticidade": "Alta",
                            "contexto_ia": f"O CNPJ {row['CNPJ_FORNECEDOR']} divergiu do padrão identificado no lote ({cnpj_padrao}).",
                        }
                    )

    def validate_encoding(self, row: pd.Series, hits: List[Dict[str, Any]]):
        enc = str(row.get("ENCODING", "")).lower()
        if enc not in ["utf-8", "ascii"]:
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Encoding inválido",
                    "slug": "encoding_invalido",
                    "criticidade": "Média",
                    "contexto_ia": f"Encoding '{enc}' não aceito.",
                }
            )

    def validate_inconsistent_dates(self, row: pd.Series, hits: List[Dict[str, Any]]):
        dt_emissao = self.parse_date(row.get("DATA_EMISSAO_NF"))
        dt_pagamento = self.parse_date(row.get("DATA_PAGAMENTO"))
        if dt_emissao and dt_pagamento and dt_emissao > dt_pagamento:
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "NF emitida após pagamento",
                    "slug": "data_inconsistente",
                    "criticidade": "Alta",
                    "contexto_ia": f"Emissão {row.get('DATA_EMISSAO_NF')} > Pagamento {row.get('DATA_PAGAMENTO')}.",
                }
            )

    def validate_status_conflict(self, row: pd.Series, hits: List[Dict[str, Any]]):
        status = str(row.get("STATUS", "")).upper()
        if "CANCELADO" in status and row.get("DATA_PAGAMENTO"):
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "STATUS inconsistente",
                    "slug": "status_conflitante",
                    "criticidade": "Média",
                    "contexto_ia": "Cancelado com data de pagamento.",
                }
            )

    def validate_value_outliers(
        self, row: pd.Series, stats_df: pd.DataFrame, hits: List[Dict[str, Any]]
    ):
        f_key = row["_tmp_fornecedor"]
        if f_key in stats_df.index:
            stats = stats_df.loc[f_key]
            mean_val = float(stats["mean"])  # type: ignore
            count_val = int(stats["count"])  # type: ignore
            val_atual = float(row["_tmp_val_numeric"])  # type: ignore
            if count_val > 1 and val_atual > (mean_val * 1.5):
                hits.append(
                    {
                        "arquivo": row["ARQUIVO_ORIGEM"],
                        "anomalia": "Valor fora da faixa do fornecedor",
                        "slug": "outlier_valor",
                        "criticidade": "Média",
                        "contexto_ia": f"Valor R$ {val_atual} acima da média do lote (R$ {mean_val:.2f}).",
                    }
                )

    def validate_parsing_errors(self, row: pd.Series, hits: List[Dict[str, Any]]):
        if not row.get("NUMERO_DOCUMENTO") or not row.get("FORNECEDOR"):
            hits.append(
                {
                    "arquivo": row["ARQUIVO_ORIGEM"],
                    "anomalia": "Arquivo não processável",
                    "slug": "erro_parsing",
                    "criticidade": "Média",
                    "contexto_ia": "Dados obrigatórios ausentes.",
                }
            )

    async def run_programmatic_audit(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        hits = []
        df["_tmp_fornecedor"] = df["FORNECEDOR"].apply(self._get_clean_name)
        df["_tmp_aprovador"] = df["APROVADO_POR"].apply(self._get_clean_name)
        df["_tmp_val_numeric"] = df["VALOR_BRUTO"].apply(self.parse_value)
        stats_por_fornecedor = df.groupby("_tmp_fornecedor")["_tmp_val_numeric"].agg(
            ["mean", "count"]
        )

        self.validate_nf_duplicates(df, hits)
        self.validate_new_providers(df, hits)
        self.validate_new_approvers(df, hits)
        self.validate_divergent_cnpj(df, hits)

        for _, row in df.iterrows():
            self.validate_encoding(row, hits)
            self.validate_hash_format(row, hits)
            self.validate_numeric_value(row, hits)
            self.validate_inconsistent_dates(row, hits)
            self.validate_status_conflict(row, hits)
            self.validate_parsing_errors(row, hits)
            self.validate_value_outliers(row, stats_por_fornecedor, hits)

        df.drop(
            columns=["_tmp_fornecedor", "_tmp_aprovador", "_tmp_val_numeric"],
            inplace=True,
        )
        return hits


anomaly_service = AnomalyService()
