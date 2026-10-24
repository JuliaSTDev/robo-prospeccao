"""Testes do armazenamento. Nenhum teste acessa o Supabase: o banco é um BancoFalso (conftest.py)."""
from datetime import date, datetime

import pytest

from robo import armazenamento
from robo.armazenamento import (
    Banco,
    carregar_leads,
    lead_para_linha,
    linha_para_lead,
    salvar_execucao,
    salvar_leads,
)
from robo.models import Execucao


# ---------- lead <-> linha ----------

def test_lead_vai_e_volta_do_banco_sem_perder_nada(criar_lead):
    lead = criar_lead(
        nome_fantasia="Escola Ação", telefone="11999999999", email="oi@escola.com.br",
        site="https://escola.com.br", site_situacao="confere", site_motivo="nome e nicho batem",
        sinais={"whatsapp_no_site", "sem_chat"}, nota=4, motivo_da_nota="WhatsApp no site, sem chat",
        coletado_em=datetime(2026, 10, 23, 18, 30, 15, 123456),
    )

    linha = lead_para_linha(lead)
    linha["status"] = "novo"          # o banco devolve o status; nós nunca o enviamos
    volta = linha_para_lead(linha)

    assert volta == lead


def test_linha_tem_data_em_texto_e_sinais_em_lista(criar_lead):
    linha = lead_para_linha(criar_lead(data_abertura=date(2010, 1, 1), sinais={"sem_chat", "meta_pixel"}))
    assert linha["data_abertura"] == "2010-01-01"
    assert linha["sinais"] == ["meta_pixel", "sem_chat"]    # em lista e ordenada


def test_status_nunca_e_enviado(criar_lead):
    """Se fosse enviado, cada execução apagaria o que a Julia marcou à mão (ex.: 'aprovado')."""
    assert "status" not in lead_para_linha(criar_lead(status="aprovado"))


def test_lead_sem_data_de_abertura_e_sem_sinais(criar_lead):
    lead = criar_lead(data_abertura=None)
    linha = lead_para_linha(lead)
    linha["status"] = "novo"
    volta = linha_para_lead(linha)
    assert volta.data_abertura is None
    assert volta.sinais == set()


def test_campos_nulos_do_banco_viram_valores_padrao(criar_lead):
    linha = lead_para_linha(criar_lead())
    linha.update({"status": None, "sinais": None, "nota": None, "site_motivo": None, "motivo_da_nota": None})
    volta = linha_para_lead(linha)
    assert (volta.status, volta.sinais, volta.nota, volta.site_motivo) == ("novo", set(), 0, "")


# ---------- salvar_leads ----------

def test_salvar_leads_envia_em_lotes_com_upsert_pelo_cnpj(criar_lead, criar_banco):
    banco = criar_banco()
    leads = [criar_lead(cnpj=f"{i:08d}000101") for i in range(5)]

    enviados = salvar_leads(leads, banco, lote=2)

    assert enviados == 5
    assert [len(linhas) for _, linhas, _ in banco.envios] == [2, 2, 1]
    assert all(tabela == "leads" and chave == "cnpj" for tabela, _, chave in banco.envios)


def test_cnpj_repetido_vira_uma_linha_so(criar_lead, criar_banco):
    """O Postgres recusa o mesmo CNPJ duas vezes no mesmo envio."""
    banco = criar_banco()
    leads = [criar_lead(cnpj="11111111000101", nota=1), criar_lead(cnpj="11111111000101", nota=7)]

    assert salvar_leads(leads, banco) == 1
    assert banco.envios[0][1][0]["nota"] == 7     # vale o último


def test_lista_vazia_nao_envia_nada(criar_banco):
    banco = criar_banco()
    assert salvar_leads([], banco) == 0
    assert banco.envios == []


# ---------- carregar_leads ----------

def test_carregar_leads_le_todas_as_paginas(monkeypatch, criar_lead, criar_banco):
    monkeypatch.setattr(armazenamento, "TAMANHO_PAGINA", 2)
    linhas = []
    for i in range(5):
        linha = lead_para_linha(criar_lead(cnpj=f"{i:08d}000101"))
        linha["status"] = "novo"
        linhas.append(linha)
    banco = criar_banco({"leads": linhas})

    leads = carregar_leads(banco)

    assert [lead.cnpj for lead in leads] == [f"{i:08d}000101" for i in range(5)]
    assert banco.leituras == [(0, 2), (2, 2), (4, 2)]    # a última página veio incompleta e parou


def test_carregar_leads_com_banco_vazio(criar_banco):
    assert carregar_leads(criar_banco()) == []


# ---------- salvar_execucao ----------

def test_salvar_execucao_grava_os_dados(criar_banco):
    banco = criar_banco()
    execucao = Execucao(parametros={"cnae": "8593700"}, qtd_leads=10, qtd_erros=1)
    execucao.data_fim = datetime.now()

    salvar_execucao(execucao, banco)

    tabela, linhas, chave = banco.envios[0]
    assert (tabela, chave) == ("execucoes", "id")
    assert linhas[0]["id"] == execucao.id
    assert linhas[0]["parametros"] == {"cnae": "8593700"}
    assert (linhas[0]["qtd_leads"], linhas[0]["qtd_erros"]) == (10, 1)


def test_execucao_sem_data_fim_vai_com_nulo(criar_banco):
    banco = criar_banco()
    salvar_execucao(Execucao(), banco)
    assert banco.envios[0][1][0]["data_fim"] is None


# ---------- Banco (sem rede) ----------

def test_chave_nova_vai_so_no_apikey():
    banco = Banco("https://abc.supabase.co/", "sb_secret_exemplo")
    assert banco.sessao.headers["apikey"] == "sb_secret_exemplo"
    assert "Authorization" not in banco.sessao.headers
    assert banco.base == "https://abc.supabase.co/rest/v1"


@pytest.mark.parametrize("url", [
    "https://abc.supabase.co",
    "https://abc.supabase.co/",
    "https://abc.supabase.co/rest/v1",      # como a página Data API mostra
    "  https://abc.supabase.co/rest/v1/  ",
])
def test_url_funciona_com_ou_sem_rest_v1(url):
    assert Banco(url, "sb_secret_exemplo").base == "https://abc.supabase.co/rest/v1"


def test_verificar_conexao_faz_uma_leitura_minima(criar_banco):
    banco = criar_banco()
    verificar_conexao(banco)
    assert banco.leituras == [(0, 1)]


def test_chave_antiga_jwt_vai_tambem_no_authorization():
    banco = Banco("https://abc.supabase.co", "eyJexemplo")
    assert banco.sessao.headers["Authorization"] == "Bearer eyJexemplo"


def test_resposta_de_erro_vira_excecao_com_o_motivo(monkeypatch):
    class RespostaRuim:
        ok = False
        status_code = 401
        text = '{"message":"Invalid API key"}'

    banco = Banco("https://abc.supabase.co", "sb_secret_exemplo")
    monkeypatch.setattr(banco.sessao, "post", lambda *args, **kwargs: RespostaRuim())

    with pytest.raises(RuntimeError, match="401.*Invalid API key"):
        banco.enviar("leads", [{"cnpj": "1"}], chave_unica="cnpj")
