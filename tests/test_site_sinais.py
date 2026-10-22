"""Testes da leitura de sinais do site. Nenhum teste acessa a internet:
o HTML vem de arquivos em tests/html e a rede é trocada por funções falsas (monkeypatch)."""
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

from robo.enriquecedores import site_sinais
from robo.enriquecedores.site_sinais import (
    enriquecer_sinais,
    ler_sinais,
    ler_sinais_do_site,
    permitido_pelo_robots_txt,
)

PASTA_HTML = Path(__file__).parent / "html"


def sopa_do_arquivo(nome: str) -> BeautifulSoup:
    return BeautifulSoup((PASTA_HTML / nome).read_text(encoding="utf-8"), "html.parser")


def sopa_de(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ---------- sinais no HTML ----------

def test_site_completo_tem_todos_os_sinais_e_chat():
    sinais = ler_sinais(sopa_do_arquivo("escola_completa.html"))
    assert sinais == {"meta_pixel", "google_tag", "whatsapp_no_site", "instagram_no_site"}
    assert "sem_chat" not in sinais   # tem o widget do tawk.to


def test_site_so_com_formulario():
    assert ler_sinais(sopa_do_arquivo("escola_so_formulario.html")) == {"so_formulario", "sem_chat"}


def test_site_vazio_so_tem_sem_chat():
    assert ler_sinais(sopa_do_arquivo("escola_vazia.html")) == {"sem_chat"}


@pytest.mark.parametrize("html, sinal", [
    ('<script src="https://connect.facebook.net/en_US/fbevents.js"></script>', "meta_pixel"),
    ("<script>fbq('init', '123');</script>", "meta_pixel"),
    ('<script src="https://www.googletagmanager.com/gtag/js?id=G-X"></script>', "google_tag"),
    ('<a href="https://wa.me/5511999999999">oi</a>', "whatsapp_no_site"),
    ('<a href="https://API.whatsapp.com/send?phone=5511">oi</a>', "whatsapp_no_site"),
    ('<a href="https://www.instagram.com/escola/">ig</a>', "instagram_no_site"),
    ("<form><input></form>", "so_formulario"),
])
def test_detecta_cada_sinal(html, sinal):
    assert sinal in ler_sinais(sopa_de(html))


def test_formulario_com_whatsapp_nao_e_so_formulario():
    sinais = ler_sinais(sopa_de('<form></form><a href="https://wa.me/1">oi</a>'))
    assert "so_formulario" not in sinais
    assert "whatsapp_no_site" in sinais


def test_widget_de_chat_tira_o_sem_chat():
    assert "sem_chat" not in ler_sinais(sopa_de('<script src="https://embed.tawk.to/abc"></script>'))


# ---------- robots.txt ----------

@pytest.mark.parametrize("robots, url, permitido", [
    ("User-agent: *\nDisallow: /", "https://x.com/", False),
    ("User-agent: *\nDisallow: /admin", "https://x.com/", True),
    ("", "https://x.com/", True),
])
def test_regras_do_robots_txt(robots, url, permitido):
    assert permitido_pelo_robots_txt(robots, url) is permitido


def test_robots_proibido_nao_visita_a_pagina(monkeypatch):
    monkeypatch.setattr(site_sinais, "robots_permite", lambda url: False)
    assert ler_sinais_do_site("https://x.com") is None


def test_site_fora_do_ar_devolve_none_sem_quebrar(monkeypatch):
    def get_falso(*args, **kwargs):
        raise requests.exceptions.ConnectionError("fora do ar")

    monkeypatch.setattr(site_sinais, "robots_permite", lambda url: True)
    monkeypatch.setattr(site_sinais.requests, "get", get_falso)
    assert ler_sinais_do_site("https://x.com") is None


# ---------- enriquecer_sinais (a rede é trocada por uma função falsa) ----------

def test_so_le_os_sites_confirmados(monkeypatch, criar_lead):
    visitados = []

    def lero_falso(url):
        visitados.append(url)
        return {"whatsapp_no_site"}

    monkeypatch.setattr(site_sinais, "ler_sinais_do_site", lero_falso)
    confirmado = criar_lead(site="https://escola.com.br", site_situacao="confere")
    de_outra = criar_lead(cnpj="22222222000101", site="https://outra.com.br", site_situacao="nao_confere")

    contagem = enriquecer_sinais([confirmado, de_outra], pausa=0, mostrar=False)

    assert visitados == ["https://escola.com.br"]
    assert confirmado.sinais == {"whatsapp_no_site"}
    assert de_outra.sinais == set()
    assert contagem["leu"] == 1


def test_site_que_nao_pode_ser_lido_nao_ganha_sinais(monkeypatch, criar_lead):
    monkeypatch.setattr(site_sinais, "ler_sinais_do_site", lambda url: None)
    lead = criar_lead(site="https://escola.com.br", site_situacao="confere")

    contagem = enriquecer_sinais([lead], pausa=0, mostrar=False)

    assert lead.sinais == set()
    assert contagem["nao_leu"] == 1


def test_dominio_repetido_e_lido_uma_vez_so(monkeypatch, criar_lead):
    chamadas = []

    def lero_falso(url):
        chamadas.append(url)
        return {"sem_chat"}

    monkeypatch.setattr(site_sinais, "ler_sinais_do_site", lero_falso)
    a = criar_lead(cnpj="11111111000101", site="https://escola.com.br", site_situacao="confere")
    b = criar_lead(cnpj="11111111000202", site="https://www.escola.com.br/", site_situacao="confere")

    enriquecer_sinais([a, b], pausa=0, mostrar=False)

    assert len(chamadas) == 1
    assert a.sinais == b.sinais == {"sem_chat"}


def test_erro_em_um_lead_nao_para_os_outros(monkeypatch, criar_lead):
    def lero_falso(url):
        if "quebra" in url:
            raise RuntimeError("erro inesperado")
        return {"sem_chat"}

    monkeypatch.setattr(site_sinais, "ler_sinais_do_site", lero_falso)
    ruim = criar_lead(cnpj="11111111000101", site="https://quebra.com.br", site_situacao="confere")
    bom = criar_lead(cnpj="22222222000101", site="https://bom.com.br", site_situacao="confere")

    contagem = enriquecer_sinais([ruim, bom], pausa=0, mostrar=False)

    assert contagem["erro"] == 1 and contagem["leu"] == 1
    assert ruim.sinais == set()
    assert bom.sinais == {"sem_chat"}
