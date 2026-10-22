"""Verifica se o site de uma empresa responde, com tentativas e variações de URL."""
import time
from dataclasses import dataclass, field

import requests

ABRIU = "abriu"
BLOQUEADO = "bloqueado"
FORA_DO_AR = "fora_do_ar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    )
}
TIMEOUT = 15


@dataclass
class ResultadoSite:
    status: str                 # ABRIU, BLOQUEADO ou FORA_DO_AR
    detalhe: str                # código HTTP ou nome do erro
    url: str                    # URL testada originalmente
    url_final: str = ""         # URL depois de redirecionamentos
    ssl_invalido: bool = False  # só abriu por http://
    html: str = field(default="", repr=False)

    def __iter__(self):
        # compatibilidade: permite "situacao, detalhe = checar_site(url)"
        return iter((self.status, self.detalhe))


def _variantes(dominio: str) -> list[str]:
    d = dominio.replace("https://", "").replace("http://", "").strip("/")
    base = d[4:] if d.startswith("www.") else d
    return [f"https://{base}", f"https://www.{base}", f"http://{base}", f"http://www.{base}"]


def checar_site(url: str) -> ResultadoSite:
    ultimo_erro = "sem_resposta"
    for tentativa_url in _variantes(url):
        for tentativa in range(2):
            try:
                r = requests.get(tentativa_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
                if r.status_code == 403:
                    return ResultadoSite(BLOQUEADO, "403", url, r.url)
                if r.status_code < 400:
                    return ResultadoSite(
                        ABRIU, str(r.status_code), url, r.url,
                        ssl_invalido=tentativa_url.startswith("http://"),
                        html=r.text,
                    )
                ultimo_erro = str(r.status_code)
                break  # erro HTTP: tenta a próxima variante
            except requests.exceptions.SSLError:
                ultimo_erro = "SSLError"
                break  # tenta a próxima variante (inclusive http://)
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                ultimo_erro = type(e).__name__
                if tentativa == 0:
                    time.sleep(2)
    return ResultadoSite(FORA_DO_AR, ultimo_erro, url)