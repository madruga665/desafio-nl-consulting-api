ANOMALLY_RULES = [
    {
        "anomalia": "NF duplicada",
        "como_detectar": "Marcar se encontrar mais de uma linha com mesmo NUMERO_DOCUMENTO e mesmo FORNECEDOR.",
        "criticidade": "Alta",
        "slug": "nf_duplicada"
    },
    {
        "anomalia": "CNPJ divergente",
        "como_detectar": "Marcar se o CNPJ_FORNECEDOR atual for diferente do CNPJ_FORNECEDOR padrão histórico deste Fornecedor.",
        "criticidade": "Alta",
        "slug": "cnpj_divergente"
    },
    {
        "anomalia": "Fornecedor sem histórico",
        "como_detectar": "Se o nome do FORNECEDOR somente uma vez no histórioco",
        "criticidade": "Alta",
        "slug": "fornecedor_novo"
    },
    {
        "anomalia": "NF emitida após pagamento",
        "como_detectar": "A data DATA_EMISSAO_NF é posterior a DATA_PAGAMENTO.",
        "criticidade": "Alta",
        "slug": "data_inconsistente"
    },
    {
        "anomalia": "Valor fora da faixa do fornecedor",
        "como_detectar": "Marcar se VALOR_BRUTO for muito superior à média histórica deste FORNEDCEDOR.",
        "criticidade": "Média",
        "slug": "outlier_valor"
    },
    {
        "anomalia": "Aprovador não reconhecido",
        "como_detectar": "Marcar se o nome em APROVADO_POR não constar na lista de aprovadores autorizados.",
        "criticidade": "Média",
        "slug": "aprovador_desconhecido"
    },
    {
        "anomalia": "STATUS inconsistente",
        "como_detectar": "Marcar se STATUS='CANCELADO' E houver valor em DATA_PAGAMENTO.",
        "criticidade": "Média",
        "slug": "status_conflitante"
    },
    {
        "anomalia": "Arquivo não processável",
        "como_detectar": "Marcar se houver erro de encoding, campos truncados ou dados corrompidos.",
        "criticidade": "Média",
        "slug": "erro_parsing"
    }
]
