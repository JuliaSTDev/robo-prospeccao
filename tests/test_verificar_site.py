"""Testes da verificação do site. A rede (checar_site) e a conferência do conteúdo
(confere_site) são trocadas por funções falsas: nenhum teste acessa a internet."""
import pytest

from robo.enriquecedores import verificar_site as vs
from robo.enriquecedores.site_responde import ABRIU, BLOQUEADO, FORA_DO_AR, ResultadoSite


def resposta(status, detalhe, url, url_final="", html=""):
    return ResultadoSite(status, detalhe, url, url_final or url, html=html)


def confere_sempre(html, nome, nicho, url=""):
    return True, "nome e nicho batem"


# ---------- aplicar_resultado: o que muda no lead em cada situação ----------

def test_confere_guarda_a_url_final(criar_lead):
    lead = criar_lead(site="https://escola.com.br")
    vs.aplicar_resultado(lead, vs.CONFERE, "nome e nicho batem", "https://www.escola.com.br/")
    assert lead.site == "https://www.escola.com.br/"
    assert lead.site_situacao == vs.CONFERE


@pytest.mark.parametrize("situacao", [vs.NAO_CONFERE, vs.SEM_SITE])
def test_site_de_outra_empresa_ou_ausente_vira_sem_site(criar_lead, situacao):
    lead = criar_lead(site="https://abril.com.br")
    vs.aplicar_resultado(lead, situacao, "motivo")
    assert lead.site is None
    assert "site_inacessivel" not in lead.sinais


def test_fora_do_ar_tira_o_site_e_marca_o_sinal(criar_lead):
    lead = criar_lead(site="https://foradoar.com.br")
    vs.aplicar_resultado(lead, vs.INACESSIVEL, "fora do ar (ConnectionError)")
    assert lead.site is None
    assert "site_inacessivel" in lead.sinais


@pytest.mark.parametrize("situacao", [vs.BLOQUEADO_SITE, vs.REVISAR])
def test_bloqueado_e_revisar_mantem_o_site(criar_lead, situacao):
    lead = criar_lead(site="https://bloqueado.com.br")
    vs.aplicar_resultado(lead, situacao, "motivo")
    assert lead.site == "https://bloqueado.com.br"


# ---------- verificar_site (um lead) ----------

def test_lead_sem_site(criar_lead):
    lead = criar_lead(site=None)
    assert vs.verificar_site(lead, "educacao") == vs.SEM_SITE
    assert lead.site is None


def test_site_fora_do_ar(monkeypatch, criar_lead):
    monkeypatch.setattr(vs, "checar_site", lambda url: resposta(FORA_DO_AR, "ConnectionError", url))
    lead = criar_lead(site="https://foradoar.com.br")

    assert vs.verificar_site(lead, "educacao", usar_ia=False) == vs.INACESSIVEL
    assert "site_inacessivel" in lead.sinais


def test_site_que_bloqueia_o_robo(monkeypatch, criar_lead):
    monkeypatch.setattr(vs, "checar_site", lambda url: resposta(BLOQUEADO, "403", url))
    lead = criar_lead(site="https://bloqueado.com.br")

    assert vs.verificar_site(lead, "educacao", usar_ia=False) == vs.BLOQUEADO_SITE
    assert lead.site == "https://bloqueado.com.br"


def test_site_que_abre_e_confere(monkeypatch, criar_lead):
    monkeypatch.setattr(
        vs, "checar_site",
        lambda url: resposta(ABRIU, "200", url, "https://www.escola.com.br/", "<html></html>"),
    )
    monkeypatch.setattr(vs, "confere_site", confere_sempre)
    lead = criar_lead(site="https://escola.com.br")

    assert vs.verificar_site(lead, "educacao", usar_ia=False) == vs.CONFERE
    assert lead.site == "https://www.escola.com.br/"


def test_site_que_abre_mas_e_de_outra_empresa(monkeypatch, criar_lead):
    monkeypatch.setattr(vs, "checar_site", lambda url: resposta(ABRIU, "200", url, html="<html></html>"))
    monkeypatch.setattr(vs, "confere_site", lambda html, nome, nicho, url="": (False, "não confere"))
    lead = criar_lead(site="https://abril.com.br")

    assert vs.verificar_site(lead, "educacao", usar_ia=False) == vs.NAO_CONFERE
    assert lead.site is None


# ---------- verificar_sites (a lista) ----------

def test_site_fora_do_ar_nao_interrompe_a_execucao(monkeypatch, criar_lead):
    """'Pronto quando' da CEC-23: um site fora do ar não para o robô."""
    def checar_falso(url):
        if "fora" in url:
            return resposta(FORA_DO_AR, "ConnectionError", url)
        return resposta(ABRIU, "200", url, html="<html></html>")

    monkeypatch.setattr(vs, "checar_site", checar_falso)
    monkeypatch.setattr(vs, "confere_site", confere_sempre)
    leads = [
        criar_lead(cnpj="11111111000101", site="https://a.com.br"),
        criar_lead(cnpj="22222222000101", site="https://fora.com.br"),
        criar_lead(cnpj="33333333000101", site="https://b.com.br"),
    ]

    contagem = vs.verificar_sites(leads, "educacao", usar_ia=False, pausa=0, mostrar=False)

    assert [lead.site_situacao for lead in leads] == [vs.CONFERE, vs.INACESSIVEL, vs.CONFERE]
    assert contagem["erro"] == 0
    assert "site_inacessivel" in leads[1].sinais


def test_dominio_repetido_e_verificado_uma_vez_so(monkeypatch, criar_lead):
    chamadas = []

    def checar_falso(url):
        chamadas.append(url)
        return resposta(ABRIU, "200", url, html="<html></html>")

    monkeypatch.setattr(vs, "checar_site", checar_falso)
    monkeypatch.setattr(vs, "confere_site", confere_sempre)
    leads = [
        criar_lead(cnpj="11111111000101", site="https://escola.com.br"),
        criar_lead(cnpj="11111111000202", site="https://www.escola.com.br/"),
    ]

    vs.verificar_sites(leads, "educacao", usar_ia=False, pausa=0, mostrar=False)

    assert len(chamadas) == 1
    assert [lead.site_situacao for lead in leads] == [vs.CONFERE, vs.CONFERE]


def test_erro_inesperado_em_um_lead_nao_para_os_outros(monkeypatch, criar_lead):
    def checar_falso(url):
        if "quebra" in url:
            raise RuntimeError("erro inesperado")
        return resposta(ABRIU, "200", url, html="<html></html>")

    monkeypatch.setattr(vs, "checar_site", checar_falso)
    monkeypatch.setattr(vs, "confere_site", confere_sempre)
    leads = [
        criar_lead(cnpj="11111111000101", site="https://quebra.com.br"),
        criar_lead(cnpj="22222222000101", site="https://bom.com.br"),
    ]

    contagem = vs.verificar_sites(leads, "educacao", usar_ia=False, pausa=0, mostrar=False)

    assert contagem["erro"] == 1
    assert leads[0].site_situacao == vs.REVISAR
    assert leads[0].site_motivo == "erro ao verificar (RuntimeError)"
    assert leads[1].site_situacao == vs.CONFERE


def test_dado_corrompido_no_lead_nao_derruba_a_execucao(criar_lead):
    ruim = criar_lead(cnpj="11111111000101", site=12345)   # site que não é texto
    bom = criar_lead(cnpj="22222222000101", site=None)

    contagem = vs.verificar_sites([ruim, bom], "educacao", usar_ia=False, pausa=0, mostrar=False)

    assert contagem["erro"] == 1
    assert ruim.site_situacao == vs.REVISAR
    assert bom.site_situacao == vs.SEM_SITE


# ---------- relatório ----------

def test_relatorio_calcula_a_hipotese(criar_lead):
    confirmado = criar_lead(site="https://a.com.br", site_situacao=vs.CONFERE)
    de_outra = criar_lead(site=None, site_situacao=vs.NAO_CONFERE)
    sem_dominio = criar_lead(site=None, site_situacao=vs.SEM_SITE)

    texto = vs.relatorio_sites([confirmado, de_outra, sem_dominio])

    assert "Total de leads:                 3" in texto
    assert "50% viraram site confirmado" in texto   # 1 de 2 que tinham domínio


def test_relatorio_sem_leads():
    assert vs.relatorio_sites([]) == "Nenhum lead."
