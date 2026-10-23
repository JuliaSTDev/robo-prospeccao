"""Testes da ficha: nome para busca, links, seleção do top e textos.
Padrão de todo teste: 1. preparar  2. executar  3. conferir."""
from datetime import date

import pytest

from robo.exportadores.ficha import (
    descrever_sinais,
    descrever_site,
    exportar_fichas,
    fora_do_perfil,
    montar_links,
    nome_para_busca,
    selecionar_top,
    uma_por_empresa,
)


# ---------- nome_para_busca ----------

def test_nome_para_busca_tira_o_sufixo_societario(criar_lead):
    lead = criar_lead(razao_social="ESCOLA ACAO LTDA")
    assert nome_para_busca(lead) == "ESCOLA ACAO"


def test_nome_fantasia_vale_mais_que_a_razao_social(criar_lead):
    lead = criar_lead(razao_social="ESCOLA ACAO LTDA", nome_fantasia="Escola Ação")
    assert nome_para_busca(lead) == "Escola Ação"


def test_espacos_sobrando_e_sufixo_me(criar_lead):
    lead = criar_lead(razao_social="ESCOLA   ACAO  ME")
    assert nome_para_busca(lead) == "ESCOLA ACAO"


@pytest.mark.parametrize("razao, esperado", [
    ("ESCOLA ACAO LTDA", "ESCOLA ACAO"),
    ("ESCOLA ACAO EPP", "ESCOLA ACAO"),
    ("ESCOLA ACAO EIRELI", "ESCOLA ACAO"),
    ("ESCOLA ACAO S/S", "ESCOLA ACAO"),
    ("ESCOLA ACAO S/A", "ESCOLA ACAO"),
    ("escola acao ltda", "escola acao"),      # minúsculas também
])
def test_varios_sufixos(criar_lead, razao, esperado):
    assert nome_para_busca(criar_lead(razao_social=razao)) == esperado


# ---------- montar_links ----------

def test_link_do_google_codifica_acentos_e_espacos():
    links = montar_links("Escola Ação", "São Paulo")
    assert links["Google"] == "https://www.google.com/search?q=Escola+A%C3%A7%C3%A3o+S%C3%A3o+Paulo"


def test_tem_os_quatro_links():
    links = montar_links("Escola Ação", "São Paulo")
    assert list(links) == ["Google", "Instagram", "Reclame Aqui", "Meta Ad Library"]


def test_link_da_meta_usa_so_o_nome():
    # a Meta Ad Library busca pelo nome, sem a cidade
    link = montar_links("Escola Ação", "São Paulo")["Meta Ad Library"]
    assert "q=Escola+A%C3%A7%C3%A3o&" in link
    assert "S%C3%A3o" not in link


# ---------- fora_do_perfil ----------

def test_associacao_fica_fora_do_perfil(criar_lead):
    assert fora_do_perfil(criar_lead(razao_social="ASSOCIACAO CULTURAL X")) is True


def test_escola_normal_esta_no_perfil(criar_lead):
    assert fora_do_perfil(criar_lead(razao_social="ESCOLA ACAO LTDA")) is False


# ---------- uma_por_empresa ----------

def test_matriz_e_filial_viram_um_lead_so_e_fica_a_matriz(criar_lead):
    filial = criar_lead(cnpj="11111111000202", matriz_filial="2")
    matriz = criar_lead(cnpj="11111111000101", matriz_filial="1")

    resultado = uma_por_empresa([filial, matriz])   # filial vem primeiro de propósito

    assert resultado == [matriz]


def test_empresas_diferentes_continuam_separadas(criar_lead):
    a = criar_lead(cnpj="11111111000101")
    b = criar_lead(cnpj="22222222000101")
    assert uma_por_empresa([a, b]) == [a, b]


# ---------- selecionar_top ----------

def test_maior_nota_vem_primeiro(criar_lead):
    baixa = criar_lead(cnpj="11111111000101", nota=2)
    alta = criar_lead(cnpj="22222222000101", nota=9)
    media = criar_lead(cnpj="33333333000101", nota=5)

    assert selecionar_top([baixa, alta, media]) == [alta, media, baixa]


def test_respeita_o_limite_n(criar_lead):
    leads = [criar_lead(cnpj=f"{i:08d}000101", nota=i) for i in range(1, 6)]
    assert len(selecionar_top(leads, n=3)) == 3


def test_empate_de_nota_prefere_quem_tem_site(criar_lead):
    sem_site = criar_lead(cnpj="11111111000101", nota=5, site=None)
    com_site = criar_lead(cnpj="22222222000101", nota=5, site="https://escola.com.br")

    assert selecionar_top([sem_site, com_site])[0] == com_site


def test_empate_de_nota_e_site_prefere_quem_tem_telefone(criar_lead):
    sem_tel = criar_lead(cnpj="11111111000101", nota=5, telefone=None)
    com_tel = criar_lead(cnpj="22222222000101", nota=5, telefone="11999999999")

    assert selecionar_top([sem_tel, com_tel])[0] == com_tel


def test_empate_total_prefere_a_empresa_mais_antiga(criar_lead):
    nova = criar_lead(cnpj="11111111000101", nota=5, data_abertura=date(2020, 1, 1))
    antiga = criar_lead(cnpj="22222222000101", nota=5, data_abertura=date(2005, 1, 1))

    assert selecionar_top([nova, antiga])[0] == antiga


def test_associacao_nao_entra_no_top_mesmo_com_nota_maxima(criar_lead):
    associacao = criar_lead(cnpj="11111111000101", razao_social="ASSOCIACAO X", nota=10)
    escola = criar_lead(cnpj="22222222000101", nota=1)

    assert selecionar_top([associacao, escola]) == [escola]


# ---------- descrever_site / descrever_sinais ----------

def test_descrever_site_confirmado(criar_lead):
    lead = criar_lead(site="https://escola.com.br", site_situacao="confere")
    assert descrever_site(lead) == "https://escola.com.br (confirmado)"


def test_descrever_site_sem_site(criar_lead):
    lead = criar_lead(site=None, site_situacao="sem_site")
    assert descrever_site(lead) == "não encontrado (sem domínio próprio no e-mail)"


def test_descrever_site_nao_verificado(criar_lead):
    lead = criar_lead(site="https://escola.com.br", site_situacao=None)
    assert descrever_site(lead) == "https://escola.com.br (não verificado)"


def test_descrever_sinais_na_ordem_da_ficha(criar_lead):
    lead = criar_lead(sinais={"sem_chat", "whatsapp_no_site"})   # set não tem ordem
    assert descrever_sinais(lead) == "WhatsApp, sem chat"


def test_descrever_sinais_vazio(criar_lead):
    assert descrever_sinais(criar_lead()) == "—"


# ---------- exportar_fichas (grava um arquivo de verdade, numa pasta temporária) ----------

def test_exportar_fichas_grava_o_arquivo(criar_lead, tmp_path):
    caminho = tmp_path / "fichas.md"
    leads = [
        criar_lead(cnpj="11111111000101", nome_fantasia="Escola Um", nota=8, motivo_da_nota="sem chat"),
        criar_lead(cnpj="22222222000101", nome_fantasia="Escola Dois", nota=3),
    ]

    exportar_fichas(leads, str(caminho), "São Paulo")

    texto = caminho.read_text(encoding="utf-8")
    assert texto.startswith("# Fichas de prospecção")
    assert "## Escola Um" in texto and "## Escola Dois" in texto
    assert "**Nota: 8/10** — sem chat" in texto
    assert "https://www.google.com/search?q=Escola+Um+S%C3%A3o+Paulo" in texto
