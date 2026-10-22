"""Verifica o site candidato de cada lead e grava o resultado no próprio lead.

Fluxo por lead:
    sem site candidato        -> sem_site
    site não abre             -> inacessivel  (sinal site_inacessivel, site = None)
    site bloqueia robô (403)  -> bloqueado    (mantém o site, não dá para conferir)
    abre e confere            -> confere      (site = URL final)
    abre e é de outra empresa -> nao_confere  (site = None, vira "sem site")
    IA com confiança baixa    -> revisar      (mantém o site para olhar à mão)
"""
import logging
import time
from collections import Counter
from urllib.parse import urlparse

from robo.enriquecedores.site_confere import confere_site
from robo.enriquecedores.site_responde import ABRIU, BLOQUEADO, checar_site
from robo.models import Lead

log = logging.getLogger(__name__)

CONFERE = "confere"
SEM_SITE = "sem_site"
NAO_CONFERE = "nao_confere"
INACESSIVEL = "inacessivel"
REVISAR = "revisar"
BLOQUEADO_SITE = "bloqueado"

DUVIDOSOS = ("nome bate", "nicho bate", "nome genérico")


def _dominio(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def aplicar_resultado(lead: Lead, situacao: str, motivo: str, url_final: str | None = None) -> None:
    """Grava no lead o que a verificação descobriu. Função pura, fácil de testar."""
    lead.site_situacao = situacao
    lead.site_motivo = motivo

    if situacao == CONFERE:
        lead.site = url_final or lead.site
    elif situacao in (NAO_CONFERE, SEM_SITE):
        lead.site = None
    elif situacao == INACESSIVEL:
        lead.site = None
        lead.sinais.add("site_inacessivel")
    # BLOQUEADO e REVISAR: mantém o site como está


def _conferir(res, lead: Lead, nicho: str, usar_ia: bool) -> tuple[str, str]:
    """Decide se o site que abriu é da empresa. Devolve (situacao, motivo)."""
    nome = lead.nome_fantasia or lead.razao_social
    ok, motivo = confere_site(res.html, nome, nicho, res.url_final)

    if not ok and usar_ia and motivo.startswith(DUVIDOSOS):
        # import aqui dentro: sem chave da Groq o resto do robô continua funcionando
        from robo.enriquecedores.site_confere_ia import confere_com_ia
        ok, motivo = confere_com_ia(res.html, nome, nicho, res.url_final)

    if motivo.startswith("IA (baixa)") or motivo.startswith("IA indisponível"):
        return REVISAR, motivo
    return (CONFERE if ok else NAO_CONFERE), motivo


def verificar_site(lead: Lead, nicho: str, usar_ia: bool = True) -> str:
    """Verifica o site de um lead e grava o resultado nele. Devolve a situação."""
    if not lead.site:
        aplicar_resultado(lead, SEM_SITE, "sem domínio próprio no e-mail")
        return SEM_SITE

    res = checar_site(lead.site)
    if res.status == BLOQUEADO:
        aplicar_resultado(lead, BLOQUEADO_SITE, "site bloqueia robô (403)")
    elif res.status != ABRIU:
        aplicar_resultado(lead, INACESSIVEL, f"fora do ar ({res.detalhe})")
    else:
        situacao, motivo = _conferir(res, lead, nicho, usar_ia)
        aplicar_resultado(lead, situacao, motivo, res.url_final)
    return lead.site_situacao


def verificar_sites(leads: list[Lead], nicho: str, usar_ia: bool = True,
                    pausa: float = 1.5, mostrar: bool = True) -> Counter:
    """Verifica todos os leads. Domínio repetido é verificado uma vez só (cache).

    Se a verificação de um lead falhar, o erro é registrado, o lead vai para 'revisar'
    e a execução continua. Os erros também são contados em contagem['erro'].
    """
    cache: dict[str, tuple[str, str, str | None]] = {}
    contagem: Counter = Counter()

    for i, lead in enumerate(leads, start=1):
        try:
            dominio = _dominio(lead.site) if lead.site else None

            if dominio and dominio in cache:
                situacao, motivo, url_final = cache[dominio]
                aplicar_resultado(lead, situacao, motivo, url_final)
            else:
                verificar_site(lead, nicho, usar_ia)
                if dominio:
                    cache[dominio] = (lead.site_situacao, lead.site_motivo, lead.site)
                    time.sleep(pausa)  # só pausa quando acessou a internet
        except Exception as erro:
            log.exception("Falha ao verificar o lead %s", lead.cnpj[:8])
            aplicar_resultado(lead, REVISAR, f"erro ao verificar ({type(erro).__name__})")
            contagem["erro"] += 1

        contagem[lead.site_situacao] += 1
        if mostrar:
            log.info("[%d/%d] %-12s %.45s %s", i, len(leads),
                     lead.site_situacao, lead.site_motivo, lead.site or "-")

    return contagem


def relatorio_sites(leads: list[Lead]) -> str:
    """Resumo que testa a hipótese: em quantos % dos leads achamos o site certo."""
    total = len(leads)
    if total == 0:
        return "Nenhum lead."
    c = Counter(lead.site_situacao for lead in leads)
    com_dominio = total - c[SEM_SITE]

    def pct(n: int, base: int = total) -> str:
        return f"{n} ({n / base:.0%})" if base else str(n)

    linhas = [
        f"Total de leads:                 {total}",
        f"Com domínio próprio no e-mail:  {pct(com_dominio)}",
        f"  Site abriu e confere:         {pct(c[CONFERE])}   <- hipótese",
        f"  Para revisar à mão:           {pct(c[REVISAR])}",
        f"  Bloqueou o robô (403):        {pct(c[BLOQUEADO_SITE])}",
        f"  Site de outra empresa:        {pct(c[NAO_CONFERE])}",
        f"  Fora do ar:                   {pct(c[INACESSIVEL])}",
        f"Sem domínio próprio:            {pct(c[SEM_SITE])}",
    ]
    if com_dominio:
        linhas.append(f"\nDos que tinham domínio, {c[CONFERE] / com_dominio:.0%} viraram site confirmado.")
    return "\n".join(linhas)


if __name__ == "__main__":
    from datetime import date

    def lead_teste(site):
        return Lead(cnpj="11111111000101", razao_social="ESCOLA TESTE LTDA", cnae="8593700",
                    municipio="7107", uf="SP", porte="03", matriz_filial="1",
                    data_abertura=date(2010, 1, 1), site=site)

    a = lead_teste("https://escola.com.br")
    aplicar_resultado(a, CONFERE, "nome e nicho batem", "https://www.escola.com.br/")
    assert a.site == "https://www.escola.com.br/" and a.site_situacao == CONFERE

    b = lead_teste("https://abril.com.br")
    aplicar_resultado(b, NAO_CONFERE, "não confere", "https://abril.com.br")
    assert b.site is None and b.site_situacao == NAO_CONFERE

    c = lead_teste("https://foradoar.com.br")
    aplicar_resultado(c, INACESSIVEL, "fora do ar (ConnectionError)")
    assert c.site is None and "site_inacessivel" in c.sinais

    d = lead_teste("https://bloqueado.com.br")
    aplicar_resultado(d, BLOQUEADO_SITE, "403")
    assert d.site == "https://bloqueado.com.br"

    e = lead_teste(None)
    assert verificar_site(e, "educacao") == SEM_SITE and e.site is None

    assert _dominio("https://www.Escola.com.br/contato") == "escola.com.br"

    # um lead com dado corrompido não derruba a execução
    ruim = lead_teste(12345)  # site que não é texto
    contagem = verificar_sites([lead_teste(None), ruim, lead_teste(None)],
                               "educacao", usar_ia=False, pausa=0, mostrar=False)
    assert contagem["erro"] == 1 and contagem[SEM_SITE] == 2
    assert ruim.site_situacao == REVISAR

    print(relatorio_sites([a, b, c, d, e]))
    print("Tudo certo")