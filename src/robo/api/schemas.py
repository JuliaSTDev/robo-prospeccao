from enum import Enum
from pydantic import BaseModel
from datetime import date, datetime
from robo.models import Lead
from robo.exportadores.ficha import montar_links, nome_para_busca
from robo.cidades import nome_da_cidade

class StatusLead(str, Enum):
    """Os status que um lead pode ter."""
    novo = "novo"
    aprovado = "aprovado"
    descartado = "descartado"
    abordado = "abordado"
    respondido = "respondido"

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




class LeadDetalhe(LeadSaida):
    """A ficha completa: tudo do LeadSaida mais o que a página do lead mostra."""
    razao_social: str
    nome_fantasia: str | None = None
    cnae: str
    uf: str
    matriz_filial: str
    site_motivo: str
    cidade: str
    coletado_em: datetime
    links: dict[str, str]    # nome do link -> endereço (Google, Instagram...)

    @classmethod
    def de_lead(cls, lead: Lead) -> "LeadDetalhe":
        """Converte o Lead do robô na ficha completa."""
        base = LeadSaida.de_lead(lead)    # reaproveita a conversão que já existe
        cidade = nome_da_cidade(lead.municipio)
        return cls(
            **base.model_dump(),          # copia todos os campos do LeadSaida
            razao_social=lead.razao_social,
            nome_fantasia=lead.nome_fantasia,   
            cnae=lead.cnae,
            uf=lead.uf,
            matriz_filial=lead.matriz_filial,
            site_motivo=lead.site_motivo,
            coletado_em=lead.coletado_em,
            cidade=cidade,
            links =montar_links(nome_para_busca(lead), cidade)

        )