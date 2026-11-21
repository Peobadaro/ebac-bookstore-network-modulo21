# Imagem base: Python (versão slim, mais leve)
FROM python:3.13-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=2.4.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

ENV PATH="$POETRY_HOME/bin:$PATH"

# Dependências do sistema
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala o Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Pasta da aplicação dentro do container
WORKDIR /app

# Copia só os arquivos de dependências primeiro (aproveita o cache do Docker)
COPY pyproject.toml poetry.lock ./

# Instala as dependências do projeto (inclui as de desenvolvimento,
# porque o settings usa django-extensions e o Debug Toolbar)
RUN poetry install --no-root

# Copia o restante do projeto
COPY . .

EXPOSE 8000

# Aplica as migrations e sobe o servidor acessível de fora do container
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
