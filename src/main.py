# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import joblib, io, json, os, uuid
import numpy as np
from pathlib import Path

PASTA_STORAGE = Path("storage")
PASTA_STORAGE.mkdir(exist_ok=True)

ARQ_MODELO   = PASTA_STORAGE / "model.pkl"
ARQ_HISTORICO = PASTA_STORAGE / "history.jsonl"

app = FastAPI(title="API Previsão de Atraso")

# -------------------- Estado em memória ------------------------
modelo_memoria = None     # objeto modelo carregado (se houver)

# -------------------- Schemas ----------------------------------
class EntradaPredicao(BaseModel):
    wind_origin: float

class SaidaPredicao(BaseModel):
    atraso_previsto: float

# -------------------- Utilidades de histórico ------------------
def append_historico(registro: dict):
    """Acrescenta 1 linha JSON a history.jsonl."""
    with ARQ_HISTORICO.open("a", encoding="utf‑8") as f:
        f.write(json.dumps(registro) + "\n")

def ler_historico():
    """Carrega todo o histórico (pode ficar pesado p/ produção)."""
    if not ARQ_HISTORICO.exists():
        return []
    with ARQ_HISTORICO.open("r", encoding="utf‑8") as f:
        return [json.loads(l) for l in f]

# -------------------- Endpoints --------------------------------
@app.get("/health/", tags=["Sistema"])
def health():
    return {"status": "ok"}


@app.post("/model/load/", tags=["Modelo"])
async def carregar_modelo(arquivo: UploadFile = File(...)):
    """
    Envia um .pkl; salva em disco e mantém cópia em memória.
    """
    global modelo_memoria
    if not arquivo.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .pkl")

    conteudo = await arquivo.read()
    try:
        modelo_memoria = joblib.load(io.BytesIO(conteudo))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler pkl: {e}")

    # grava em disco
    with ARQ_MODELO.open("wb") as f:
        f.write(conteudo)

    return {"status": "modelo carregado e salvo"}


@app.post("/model/predict/", response_model=SaidaPredicao, tags=["Modelo"])
def prever(payload: EntradaPredicao):
    """
    Recebe JSON, devolve previsão e persiste no histórico.
    """
    global modelo_memoria

    # garante modelo na memória; se não, tenta carregar do disco
    if modelo_memoria is None:
        if not ARQ_MODELO.exists():
            raise HTTPException(status_code=503, detail="Modelo não carregado")
        modelo_memoria = joblib.load(ARQ_MODELO)

    # faz predição (scikit-learn)
    atraso = float(modelo_memoria.predict(np.array([[payload.wind_origin]]))[0])

    # grava histórico
    registro = {
        "id": uuid.uuid4().hex,
        "entrada": payload.dict(),
        "saida": atraso,
    }
    append_historico(registro)

    return {"atraso_previsto": atraso}


@app.get("/model/history/", tags=["Modelo"])
def historico():
    """
    Retorna a lista completa de predições já realizadas.
    """
    return ler_historico()