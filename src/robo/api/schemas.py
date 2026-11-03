from enum import Enum
from pydantic import BaseModel
from datetime import date
from robo.models import Lead

class StatusLead(str, Enum):
    """Os status que um lead pode ter."""
    novo = "novo"
    aprovado = "aprovado"
    descartado = "descartado"
    abordado = "abordado"


class StatusEntrada(BaseModel):
    """Corpo do PATCH: {"status": "aprovado"}."""
    status: StatusLead

class LeadSaida(BaseModel):
    """Um lead como a API mostra: o que o painel precisa para decidir."""
    cnpj: str
    nome: str
    nota: int
    motivo_da_nota: str
    sinais: list[str]
    status: str
    municipio: str  
    porte: str
    telefone: str | None = None
    email: str | None = None
    site: str | None = None
    site_situacao: str | None = None
    data_abertura: date | None = None
    @classmethod
    def de_lead(cls, lead: Lead) -> "LeadSaida":
        """Converte o Lead do robô (dataclass) no formato da API."""
        return cls(
            cnpj=lead.cnpj,
            nome=lead.nome_fantasia or lead.razao_social,
            nota=lead.nota,
            motivo_da_nota=lead.motivo_da_nota,
            sinais=sorted(lead.sinais),
            status=lead.status,
            telefone= lead.telefone,
            email=lead.email,
            site=lead.site,
            site_situacao=lead.site_situacao,
            municipio=lead.municipio, 
            porte=lead.porte,
            data_abertura=lead.data_abertura
        )