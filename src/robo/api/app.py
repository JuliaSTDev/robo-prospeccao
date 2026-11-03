"""API do robô: lista os leads e muda o status deles.

Para rodar (na raiz do projeto, com o ambiente ativado):
    uvicorn robo.api.app:app --reload
Depois abra http://127.0.0.1:8000/docs
"""
import logging
from functools import lru_cache

import requests
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from robo.api.schemas import LeadSaida, StatusEntrada, StatusLead
from robo.armazenamento import atualizar_status, conectar, listar_leads

log = logging.getLogger(__name__)

app = FastAPI(title="Robô de prospecção")


@lru_cache
def obter_banco():
    """Conecta ao Supabase uma vez só e reaproveita. Nos testes, este é o ponto que se troca por um banco falso."""
    return conectar()


@app.exception_handler(RuntimeError)
@app.exception_handler(requests.RequestException)
def banco_indisponivel(request: Request, erro: Exception):
    """Supabase recusou ou ficou fora do ar: devolve 502, sem mostrar detalhes internos."""
    # o motivo real vai para o terminal (quem chama a API não precisa ver isso)
    log.error("Falha ao falar com o banco", exc_info=erro)
    return JSONResponse(status_code=502, content={"detail": "Banco de dados indisponível"})


@app.get("/saude")
def saude():
    """Só responde que está no ar (não toca no banco)."""
    return {"status": "ok"}


@app.get("/leads", response_model=list[LeadSaida])
def listar(
    status: StatusLead | None = None,
    limite: int = Query(50, ge=1, le=200),
    banco=Depends(obter_banco),
):
    """Os leads de maior nota primeiro. Aceita ?status=novo e ?limite=10."""
    leads = listar_leads(banco, status=status.value if status else None, limite=limite)
    return [LeadSaida.de_lead(lead) for lead in leads]


@app.patch("/leads/{cnpj}/status", response_model=LeadSaida)
def mudar_status(
    entrada: StatusEntrada,
    cnpj: str = Path(pattern=r"^\d{14}$"),
    banco=Depends(obter_banco),
):
    """Muda o status de um lead (novo, aprovado, descartado, abordado)."""
    lead = atualizar_status(banco, cnpj, entrada.status.value)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return LeadSaida.de_lead(lead)
