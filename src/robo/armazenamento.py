
import logging
import os
import requests
from robo.cidades import nome_da_cidade
from robo.exportadores.ficha import montar_links, nome_para_busca
from robo.models import Execucao, Lead
from datetime import date, datetime

log = logging.getLogger(__name__)

TAMANHO_LOTE = 500      # quantas linhas vão em cada envio
TAMANHO_PAGINA = 1000   # o Supabase devolve no máximo 1000 linhas por consulta


class Banco:
    """Cliente mínimo do Supabase: enviar linhas (upsert) e ler linhas."""

    def __init__(self, url: str, chave: str):
        endereco = url.strip().rstrip("/")
        if endereco.endswith("/rest/v1"):   # a página Data API mostra a URL já com /rest/v1
            endereco = endereco[: -len("/rest/v1")]
        self.base = endereco + "/rest/v1"
        self.sessao = requests.Session()
        self.sessao.headers.update({"apikey": chave, "Content-Type": "application/json"})
        if chave.startswith("eyJ"):   # chave antiga (service_role) é um JWT e vai também no Authorization
            self.sessao.headers["Authorization"] = f"Bearer {chave}"

    def enviar(self, tabela: str, linhas: list[dict], chave_unica: str) -> None:
        """Upsert: se a chave única já existe, atualiza a linha; se não, cria."""
        resposta = self.sessao.post(
            f"{self.base}/{tabela}",
            params={"on_conflict": chave_unica},
            json=linhas,
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            timeout=60,
        )
        _conferir(resposta)

    def ler(self, tabela: str, ordem: str, inicio: int, quantidade: int,
            filtros: dict[str, str] | None = None, descendente: bool = False) -> list[dict]:

            ordenacao = f"{ordem}.desc,cnpj.asc" if descendente else f"{ordem}.asc"
            params = {"select": "*", "order": ordenacao, "offset": inicio, "limit": quantidade}
        
            for coluna, valor in (filtros or {}).items():
                params[coluna] = f"eq.{valor}"
        
            resposta = self.sessao.get(f"{self.base}/{tabela}", params=params, timeout=60)
            _conferir(resposta)
            return resposta.json()

    def atualizar(self, tabela: str, filtros: dict[str, str], valores: dict) -> list[dict]:
    
        params = {coluna: f"eq.{valor}" for coluna, valor in (filtros or {}).items()}
        resposta = self.sessao.patch(
            f"{self.base}/{tabela}",
            params=params,
            json=valores,
            headers={"Prefer": "return=representation"},
            timeout=60,
        )
        _conferir(resposta)
        return resposta.json()


def _conferir(resposta) -> None:
    """Se o Supabase recusou, levanta um erro com o motivo (vem no corpo da resposta)."""
    if not resposta.ok:
        raise RuntimeError(f"Supabase respondeu {resposta.status_code}: {resposta.text[:300]}")


def verificar_conexao(banco) -> None:
    """Faz uma leitura mínima. Se a URL, a chave ou as tabelas estiverem erradas, falha AQUI,
    em 1 segundo, e não depois de 50 minutos de execução."""
    banco.ler("leads", ordem="cnpj", inicio=0, quantidade=1)


def conectar() -> Banco:
    """Cria o banco com as chaves do arquivo .env (que NUNCA vai para o Git)."""
    from dotenv import load_dotenv

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    chave = os.getenv("SUPABASE_KEY")
    if not url or not chave:
        raise RuntimeError("Faltam SUPABASE_URL e SUPABASE_KEY no arquivo .env")
    return Banco(url, chave)


def lead_para_linha(lead: Lead) -> dict:
    """Converte o Lead no formato do banco (data vira texto, set vira lista).

    O status NÃO vai de propósito: no primeiro envio o banco coloca 'novo' sozinho,
    e nos envios seguintes o status que a Julia mudou à mão não é sobrescrito.
    A cidade e os links de verificação são calculados aqui e gravados prontos,
    para o painel (que não roda Python) só ler.
    """
    cidade = nome_da_cidade(lead.municipio)
    return {
        "cnpj": lead.cnpj,
        "razao_social": lead.razao_social,
        "nome_fantasia": lead.nome_fantasia,
        "cnae": lead.cnae,
        "municipio": lead.municipio,
        "uf": lead.uf,
        "porte": lead.porte,
        "matriz_filial": lead.matriz_filial,
        "data_abertura": lead.data_abertura.isoformat() if lead.data_abertura else None,
        "telefone": lead.telefone,
        "email": lead.email,
        "site": lead.site,
        "site_situacao": lead.site_situacao,
        "site_motivo": lead.site_motivo,
        "sinais": sorted(lead.sinais),
        "nota": lead.nota,
        "motivo_da_nota": lead.motivo_da_nota,
        "cidade": cidade,
        "links": montar_links(nome_para_busca(lead), cidade),
        "coletado_em": lead.coletado_em.isoformat(),
    }


def linha_para_lead(linha: dict) -> Lead:
    """O caminho de volta: linha do banco -> Lead."""
    abertura = linha.get("data_abertura")
    return Lead(
        cnpj=linha["cnpj"],
        razao_social=linha["razao_social"],
        cnae=linha["cnae"],
        municipio=linha["municipio"],
        uf=linha["uf"],
        porte=linha["porte"],
        matriz_filial=linha["matriz_filial"],
        data_abertura=date.fromisoformat(abertura) if abertura else None,
        nome_fantasia=linha.get("nome_fantasia"),
        telefone=linha.get("telefone"),
        email=linha.get("email"),
        site=linha.get("site"),
        site_situacao=linha.get("site_situacao"),
        site_motivo=linha.get("site_motivo") or "",
        sinais=set(linha.get("sinais") or []),
        nota=linha.get("nota") or 0,
        motivo_da_nota=linha.get("motivo_da_nota") or "",
        status=linha.get("status") or "novo",
        coletado_em=datetime.fromisoformat(linha["coletado_em"]),
    )


def salvar_leads(leads: list[Lead], banco, lote: int = TAMANHO_LOTE) -> int:
    """Grava os leads em lotes (upsert pelo CNPJ). Devolve quantas linhas foram enviadas."""
    por_cnpj = {lead.cnpj: lead_para_linha(lead) for lead in leads}   # CNPJ repetido vira uma linha só
    linhas = list(por_cnpj.values())
    for inicio in range(0, len(linhas), lote):
        banco.enviar("leads", linhas[inicio:inicio + lote], chave_unica="cnpj")
    log.info("%d leads salvos no banco", len(linhas))
    return len(linhas)


def carregar_leads(banco) -> list[Lead]:
    """Lê todos os leads do banco, página por página (o Supabase corta em 1000)."""
    leads: list[Lead] = []
    inicio = 0
    while True:
        linhas = banco.ler("leads", ordem="cnpj", inicio=inicio, quantidade=TAMANHO_PAGINA)
        leads.extend(linha_para_lead(linha) for linha in linhas)
        if len(linhas) < TAMANHO_PAGINA:
            break
        inicio += TAMANHO_PAGINA
    log.info("%d leads carregados do banco", len(leads))
    return leads


def salvar_execucao(execucao: Execucao, banco) -> None:
    """Registra a execução (início, fim, parâmetros, contagens)."""
    linha = {
        "id": execucao.id,
        "data_inicio": execucao.data_inicio.isoformat(),
        "data_fim": execucao.data_fim.isoformat() if execucao.data_fim else None,
        "parametros": execucao.parametros,
        "qtd_leads": execucao.qtd_leads,
        "qtd_erros": execucao.qtd_erros,
    }
    banco.enviar("execucoes", [linha], chave_unica="id")


def listar_leads(banco, status: str | None = None, limite: int = 50) -> list[Lead]:
    """Os leads de maior nota primeiro. Com `status`, só os que estão nesse status."""
    filtros = {"status": status} if status else None
    linhas = banco.ler("leads", ordem="nota", inicio=0, quantidade=limite, filtros=filtros, descendente=True)
    leads: list[Lead] = [linha_para_lead(linha) for linha in linhas]
    return leads


def atualizar_status(banco, cnpj: str, status: str) -> Lead | None:
    """Muda o status de um lead. Devolve o lead atualizado, ou None se o CNPJ não existe."""
    linhas = banco.atualizar("leads", filtros={"cnpj": cnpj}, valores={"status": status})
    return linha_para_lead(linhas[0]) if linhas else None


def buscar_lead(banco, cnpj: str) -> Lead | None:
    """Um lead pelo CNPJ, ou None se não existe."""
    linhas = banco.ler("leads", ordem="cnpj", inicio=0, quantidade=1, filtros={"cnpj": cnpj})
    return linha_para_lead(linhas[0]) if linhas else None