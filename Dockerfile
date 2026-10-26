FROM python:3.15-slim

# UTF-8 e log sem atraso (o Python guarda texto antes de mostrar)
ENV PYTHONUTF8=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependências primeiro: essa camada só refaz quando o requirements.txt muda
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código do robô
COPY pyproject.toml main.py ./
COPY src ./src
COPY tests ./tests
RUN pip install --no-deps -e .

# As chaves (.env) e os dados (data/) NÃO entram na imagem: entram na hora do "docker run"
CMD ["python", "main.py"]
