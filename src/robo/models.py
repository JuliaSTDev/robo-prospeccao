from datetime import date, datetime
from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class Sinal:
    lead_cnpj: str 
    fonte: str
    tipo: str
    valor: str
    coletado_em: datetime = field(default_factory=datetime.now)

@dataclass
class Lead:
    cnpj: str
    razao_social: str
    cnae: str
    municipio: str
    uf: str
    porte: str
    matriz_filial: str
    data_abertura: date | None
    nome_fantasia: str | None = None
    telefone: str | None = None
    email: str | None = None
    site: str | None = None
    site_situacao: str | None = None  # confere, sem_site, nao_confere, inacessivel, bloqueado, revisar
    site_motivo: str = ""              # por que chegou nessa situação
    sinais: set[str] = field(default_factory=set)  # sinais detectados pelos enriquecedores
    nota: int = 0
    motivo_da_nota: str = ""
    status: str = "novo"
    coletado_em: datetime = field(default_factory=datetime.now)

@dataclass
class Execucao:
    id: str = field(default_factory=lambda: uuid4().hex)
    data_inicio: datetime = field(default_factory=datetime.now)
    data_fim: datetime | None = None
    parametros: dict[str, str] = field(default_factory=dict) 
    qtd_leads: int = 0
    qtd_erros: int = 0