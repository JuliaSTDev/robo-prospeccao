"""Lê a página inicial de um site e detecta sinais de marketing no HTML.

Regras de boa conduta: respeita o robots.txt, faz UMA visita por site, usa timeout
e se identifica com um User-Agent claro. Erro de leitura nunca quebra o robô.
"""
import time
from collections import Counter
from datetime import date
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from robo.enriquecedores.verificar_site import CONFERE
from robo.models import Lead

USER_AGENT = "robo-prospeccao/0.1 (projeto de estudo; +https://github.com/JuliaSTDev/robo-prospeccao)"
TIMEOUT_SEGUNDOS = 8

PADROES_WHATSAPP = ("wa.me", "api.whatsapp.com", "web.whatsapp.com")
PADROES_INSTAGRAM = ("instagram.com",)
PADROES_PIXEL = ("connect.facebook.net", "fbq(")
PADROES_GOOGLE_TAG = ("googletagmanager.com", "gtag(")
PADROES_CHAT = ("tawk.to", "jivosite", "crisp.chat", "tidio", "zdassets.com", "intercom", "livechatinc")


def contem_algum(texto: str, padroes: tuple[str, ...]) -> bool:
    """True se algum dos padrões aparece dentro do texto."""
    return any(padrao in texto for padrao in padroes)


def tem_link_para(sopa: BeautifulSoup, padroes: tuple[str, ...]) -> bool:
    """True se a página tem algum link (<a href>) que contém um dos padrões."""
    for link in sopa.find_all("a", href=True):
        if contem_algum(link["href"].lower(), padroes):
            return True
    return False


def texto_dos_scripts(sopa: BeautifulSoup) -> str:
    """Junta, em minúsculas, o endereço (src) e o conteúdo de todos os <script>."""
    partes = []
    for script in sopa.find_all("script"):
        partes.append(script.get("src", ""))
        partes.append(script.string or "")
    return " ".join(partes).lower()


def ler_sinais(sopa: BeautifulSoup) -> set[str]:
    """Sinais detectados no HTML. Os nomes de pontuacao.PESOS valem na nota; os outros ficam só registrados."""
    sinais = set()
    scripts = texto_dos_scripts(sopa)
    if contem_algum(scripts, PADROES_PIXEL):
        sinais.add("meta_pixel")
    if contem_algum(scripts, PADROES_GOOGLE_TAG):
        sinais.add("google_tag")
    if tem_link_para(sopa, PADROES_WHATSAPP):
        sinais.add("whatsapp_no_site")
    if tem_link_para(sopa, PADROES_INSTAGRAM):
        sinais.add("instagram_no_site")
    if sopa.find("form") is not None and "whatsapp_no_site" not in sinais:
        sinais.add("so_formulario")
    if not contem_algum(scripts, PADROES_CHAT):
        sinais.add("sem_chat")
    return sinais


def permitido_pelo_robots_txt(conteudo: str, url: str) -> bool:
    """Aplica as regras de um robots.txt (já baixado, em texto) à URL."""
    leitor = RobotFileParser()
    leitor.parse(conteudo.splitlines())
    return leitor.can_fetch(USER_AGENT, url)


def robots_permite(url: str) -> bool:
    """Baixa o robots.txt do site e diz se o robô pode ler a URL."""
    partes = urlparse(url)
    robots_url = f"{partes.scheme}://{partes.netloc}/robots.txt"
    try:
        resposta = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException:
        return True  # sem robots.txt acessível; se o site estiver fora do ar, a leitura da página falha depois
    if resposta.status_code in (401, 403):
        return False
    if resposta.status_code >= 400:
        return True  # 404 etc.: o site não tem robots.txt
    return permitido_pelo_robots_txt(resposta.text, url)


def ler_sinais_do_site(url: str) -> set[str] | None:
    """Lê a página inicial e devolve os sinais. None se não deu para ler (robots, erro, página com erro)."""
    if not robots_permite(url):
        return None
    try:
        resposta = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SEGUNDOS, allow_redirects=True)
    except requests.exceptions.RequestException:
        return None
    if resposta.status_code >= 400:
        return None
    return ler_sinais(BeautifulSoup(resposta.text, "html.parser"))


def _dominio(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def enriquecer_sinais(leads: list[Lead], pausa: float = 1.5, mostrar: bool = True) -> Counter:
    """Lê os sinais dos sites confirmados (situação 'confere') e grava em lead.sinais.

    Quem não está 'confere' é ignorado: sinal de site de outra empresa não vale.
    Domínio repetido é lido uma vez só. Se não der para ler, o lead segue sem sinais novos.
    """
    contagem: Counter = Counter()
    cache: dict[str, set[str] | None] = {}
    candidatos = [lead for lead in leads if lead.site_situacao == CONFERE and lead.site]

    for i, lead in enumerate(candidatos, start=1):
        dominio = _dominio(lead.site)
        if dominio not in cache:
            cache[dominio] = ler_sinais_do_site(lead.site)
            time.sleep(pausa)  # só pausa quando acessou a internet
        sinais = cache[dominio]

        if sinais is None:
            contagem["nao_leu"] += 1
        else:
            lead.sinais.update(sinais)
            contagem["leu"] += 1
        if mostrar:
            print(f"[{i}/{len(candidatos)}] {'leu' if sinais is not None else 'não leu':<8} {lead.site}")

    return contagem


if __name__ == "__main__":
    def sopa_de(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    # sinais (sem internet: HTML escrito na mão)
    assert ler_sinais(sopa_de("<p>oi</p>")) == {"sem_chat"}
    assert "meta_pixel" in ler_sinais(sopa_de('<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'))
    assert "meta_pixel" in ler_sinais(sopa_de("<script>fbq('init', '123');</script>"))
    assert "google_tag" in ler_sinais(sopa_de('<script src="https://www.googletagmanager.com/gtag/js?id=G-X"></script>'))
    assert "whatsapp_no_site" in ler_sinais(sopa_de('<a href="https://wa.me/5511999999999">oi</a>'))
    assert "instagram_no_site" in ler_sinais(sopa_de('<a href="https://www.instagram.com/escola/">ig</a>'))
    assert "sem_chat" not in ler_sinais(sopa_de('<script src="https://embed.tawk.to/abc"></script>'))
    assert "so_formulario" in ler_sinais(sopa_de("<form><input></form>"))
    assert "so_formulario" not in ler_sinais(sopa_de('<form></form><a href="https://wa.me/1">oi</a>'))

    # robots.txt (sem internet: texto escrito na mão)
    assert permitido_pelo_robots_txt("User-agent: *\nDisallow: /", "https://x.com/") is False
    assert permitido_pelo_robots_txt("User-agent: *\nDisallow: /admin", "https://x.com/") is True
    assert permitido_pelo_robots_txt("", "https://x.com/") is True

    # enriquecer_sinais ignora quem não está 'confere' (sem internet: nenhum site é visitado)
    lead = Lead(cnpj="11111111000101", razao_social="ESCOLA TESTE LTDA", cnae="8593700", municipio="7107",
                uf="SP", porte="03", matriz_filial="1", data_abertura=date(2010, 1, 1),
                site="https://escola-teste.com.br", site_situacao="nao_confere")
    assert enriquecer_sinais([lead], pausa=0, mostrar=False) == Counter()
    assert lead.sinais == set()

    print("Testes ok")

    # site de verdade
    print(sorted(ler_sinais_do_site("https://captai-landing.vercel.app") or []))