# Desafio NL Consulting - Backend Auditoria Inteligente

Este é o backend do sistema de auditoria de documentos fiscais. A aplicação processa lotes de arquivos `.txt` compactados em `.zip`, identifica anomalias de forma programática e utiliza Inteligência Artificial (Google Gemini) para enriquecer os resultados com explicações técnicas e recomendações.

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.14
- **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) (Assíncrono)
- **Banco de Dados:** PostgreSQL (Produção) / SQLite (Desenvolvimento)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Sintaxe Mapped/MappedColumn)
- **Migrações:** [Alembic](https://alembic.sqlalchemy.org/)
- **Processamento de Dados:** [Pandas](https://pandas.pydata.org/) e [OpenPyXL](https://openpyxl.readthedocs.io/)
- **Inteligência Artificial:** [Google GenAI SDK](https://github.com/google/generative-ai-python) (Modelos Gemini 2.5/2.0)
- **Gestão de Dependências:** [Poetry](https://python-poetry.org/)
- **Containerização:** Docker e Docker Compose

## 🏗️ Estrutura do Projeto

```text
backend/
├── app/
│   ├── api/v1/             # Rotas da API (Endpoints)
│   ├── core/               # Configurações globais e Database
│   ├── models/             # Definição das tabelas (SQLAlchemy)
│   ├── repositories/       # Camada de persistência (Acesso a dados)
│   ├── schemas/            # Modelos de validação (Pydantic)
│   └── services/           # Regras de negócio e orquestração
│       ├── ai_service.py      # Integração e resiliência com Gemini
│       ├── anomaly_service.py # Detecção programática de anomalias
│       └── document_service.py# Processamento de arquivos e Excel
├── migrations/             # Histórico de versões do banco de dados
├── anomally_rules.py       # Centralização das regras de auditoria
├── docker-compose.yml      # Orquestração para desenvolvimento
├── Dockerfile              # Imagem preparada para produção (Render.com)
└── pyproject.toml          # Dependências do Poetry
```

## 🧠 Decisões de Arquitetura

1. **Auditoria Híbrida:**
   - A detecção de erros (Duplicidade, Datas, CNPJ, Outliers) é feita via **Código (Pandas)** para garantir 100% de precisão lógica e performance instantânea.
   - A **IA (Gemini)** é usada apenas no final para "redação", preenchendo as colunas de Explicação e Recomendação com base no contexto encontrado pelo código.
2. **Resiliência Multi-Modelo:** Implementamos uma estratégia de *Fallback*. Se o modelo principal falhar ou atingir cota (429/503), o sistema tenta automaticamente modelos secundários (`flash-lite`, `flash-stable`, `pro`).
3. **Processamento em Lotes (Chunking):** O sistema processa anomalias em blocos de 50 para garantir que a resposta da IA nunca seja cortada por limites técnicos do provedor.
4. **Relacionamento de Dados:** Os documentos são vinculados a Fornecedores e Aprovadores no banco de dados, permitindo a construção de um histórico estatístico para detecção de anomalias futuras.

## 📋 Regras de Anomalia Implementadas

- **NF duplicada:** Mesmo número e fornecedor no mesmo lote.
- **CNPJ divergente:** Identifica o CNPJ minoritário para um fornecedor dentro do lote.
- **Fornecedor sem histórico:** Fornecedor que aparece apenas uma vez no lote.
- **Aprovador novo:** Aprovador que aparece apenas uma vez no lote.
- **NF emitida após pagamento:** Lógica cronológica `DATA_EMISSAO_NF > DATA_PAGAMENTO`.
- **STATUS inconsistente:** Ex: Notas canceladas com data de pagamento preenchida.
- **Valor fora da faixa:** Notas com valor acima da média do fornecedor no lote.
- **Hash inválido:** Validação de padrão Regex `[A-Z]{3}\d{10}`.
- **Encoding inválido:** Aceita apenas UTF-8 e ASCII.

## 🛠️ Como Rodar

### Pré-requisitos

- Criar um arquivo `.env` baseado no `.env.example` e preencher a `GOOGLE_API_KEY`.

### Via Docker (Recomendado)

```bash
docker-compose up --build
```

A API estará disponível em `http://localhost:8000/docs`

### Sem Docker

1. Instale as dependências:

   ```bash
   poetry install
   ```

2. Rode as migrações do banco:

   ```bash
   PYTHONPATH=. poetry run alembic upgrade head
   ```

3. Inicie o servidor:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```
