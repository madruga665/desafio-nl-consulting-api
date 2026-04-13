# Estágio de construção
FROM python:3.14-slim AS builder

WORKDIR /app

# Instalar dependências do sistema necessárias para compilar pacotes
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_VERSION=2.3.3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copiar arquivos de configuração do Poetry
COPY pyproject.toml poetry.lock ./

# Configurar o Poetry para não criar ambiente virtual dentro do container
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Estágio final
FROM python:3.14-slim

WORKDIR /app

# Instalar libpq para o PostgreSQL
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Copiar dependências instaladas do builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar o código da aplicação
COPY . .

# Variáveis de ambiente padrão
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor a porta do FastAPI
EXPOSE 8000

# Comando para iniciar a aplicação
# Executa as migrações do Alembic antes de subir o servidor
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
