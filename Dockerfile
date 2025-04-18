# Imagem base enxuta com Python 3.11
FROM python:3.11-slim

# Evita arquivos .pyc e mantém log em tempo‑real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do contêiner
WORKDIR /app

# ───────────────────────────────────────────────
# 1. Instala dependências
#    (copiamos requirements.txt primeiro p/ aproveitar cache)
# ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────────────────────────────────────────────
# 2. Copia código‑fonte e diretório de storage
# ───────────────────────────────────────────────
COPY src/ ./src
RUN mkdir -p storage                    # cria pasta para modelo/histórico

# ───────────────────────────────────────────────
# 3. Expõe porta 8000 e define comando default
# ───────────────────────────────────────────────
EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]