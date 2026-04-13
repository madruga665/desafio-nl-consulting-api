# Estágio de construção
FROM python:3.14-slim AS builder

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
ENV POETRY_VERSION=2.3.3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copiar arquivos de configuração e instalar dependências
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Estágio final
FROM python:3.14-slim

WORKDIR /app

# Instalar libpq para o PostgreSQL e curl para healthchecks
RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*

# Copiar dependências do builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar o código da aplicação
COPY . .

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Porta padrão (o Render sobrescreve isso via variável $PORT)
EXPOSE 8000

# Comando de inicialização otimizado para produção:
# 1. alembic upgrade head: Garante que o banco está atualizado
# 2. fastapi run: Comando moderno do FastAPI para produção
CMD ["sh", "-c", "alembic upgrade head && fastapi run app/main.py --port ${PORT:-8000}"]
