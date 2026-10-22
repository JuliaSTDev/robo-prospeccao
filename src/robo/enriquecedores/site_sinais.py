"""Lê a página inicial de um site e detecta sinais de marketing no HTML.

Regras de boa conduta: respeita o robots.txt, faz UMA visita por site, usa timeout
e se identifica com um User-Agent claro.
"""
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

USER_AGENT = "robo-prospeccao/0.1 (projeto de estudo; +https://github.com/JuliaSTDev/robo-prospeccao)"
TIMEOUT_SEGUNDOS = 8

PADROES_WHATSAPP = ("wa.me", "api.whatsapp.com", "web.whatsapp.com")
PADROES_PIXEL = ("connect.facebook.net", "fbq(")
PADROES_GOOGLE_TAG = ("googletagmanager.com", "gtag(")
PADROES_CHAT = ("tawk.to", "jivosite", "crisp.chat", "tidio", "zdassets.com", "intercom", "livechatinc")


def contem_algum(texto: str, padroes: tuple[str, ...]) -> bool:
    """True se algum dos padrões aparece dentro do texto."""
    return any(padrao in texto for padrao in padroes)


def tem_whatsapp(sopa: BeautifulSoup) -> bool:
    """Devolve True se a página tem algum link para o WhatsApp."""
    for link in sopa.find_all("a", href=True):
        if contem_algum(link["href"].lower(), PADROES_WHATSAPP):
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
    """Sinais detectados no HTML, com os mesmos nomes de pontuacao.PESOS."""
    sinais = set()
    scripts = texto_dos_scripts(sopa)
    if contem_algum(scripts, PADROES_PIXEL):
        sinais.add("meta_pixel")
    if contem_algum(scripts, PADROES_GOOGLE_TAG):
        sinais.add("google_tag")
    if tem_whatsapp(sopa):
        sinais.add("whatsapp_no_site")
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


if __name__ == "__main__":
    def sopa_de(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    # sinais (sem internet: HTML escrito na mão)
    assert ler_sinais(sopa_de("<p>oi</p>")) == {"sem_chat"}
    assert "meta_pixel" in ler_sinais(sopa_de('<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'))
    assert "meta_pixel" in ler_sinais(sopa_de("<script>fbq('init', '123');</script>"))
    assert "google_tag" in ler_sinais(sopa_de('<script src="https://www.googletagmanager.com/gtag/js?id=G-X"></script>'))
    assert "whatsapp_no_site" in ler_sinais(sopa_de('<a href="https://wa.me/5511999999999">oi</a>'))
    assert "sem_chat" not in ler_sinais(sopa_de('<script src="https://embed.tawk.to/abc"></script>'))

    # robots.txt (sem internet: texto escrito na mão)
    assert permitido_pelo_robots_txt("User-agent: *\nDisallow: /", "https://x.com/") is False
    assert permitido_pelo_robots_txt("User-agent: *\nDisallow: /admin", "https://x.com/") is True
    assert permitido_pelo_robots_txt("", "https://x.com/") is True
    print("Testes ok")

    # site de verdade
    print(sorted(ler_sinais_do_site("https://captai-landing.vercel.app") or []))