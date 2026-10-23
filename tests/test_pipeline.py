"""Testes do pipeline. A coleta e as etapas lentas são trocadas por funções falsas."""
from collections import Counter

from robo import pipeline


def test_email_invalido_nao_derruba_os_outros_leads(criar_lead):
    leads = [
        criar_lead(email="contato@escola.com.br"),
        criar_lead(email="semarroba"),     # sem @: a extração do domínio dá erro
        criar_lead(email=None),
    ]

    erros = pipeline.definir_sites_candidatos(leads)

    assert erros == 1
    assert leads[0].site == "https://escola.com.br"
    assert leads[1].site is None and leads[2].site is None


def test_modo_rapido_registra_a_execucao(monkeypatch, criar_lead, tmp_path):
    leads = [criar_lead(email="contato@escola.com.br"), criar_lead(cnpj="22222222000101", email="semarroba")]
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: leads)
    saida = tmp_path / "fichas.md"

    execucao = pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(saida), rapido=True,
    )

    assert execucao.qtd_leads == 2
    assert execucao.qtd_erros == 1            # o e-mail sem @
    assert execucao.data_fim is not None
    assert execucao.data_fim >= execucao.data_inicio
    assert execucao.parametros["rapido"] == "True"
    assert saida.exists()                     # a ficha foi gravada


def test_erros_das_etapas_sao_somados(monkeypatch, criar_lead, tmp_path):
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead(email="contato@escola.com.br")])
    monkeypatch.setattr(pipeline, "verificar_sites", lambda leads, nicho, usar_ia: Counter({"erro": 2}))
    monkeypatch.setattr(pipeline, "enriquecer_sinais", lambda leads: Counter({"erro": 1}))

    execucao = pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), usar_ia=False,
    )

    assert execucao.qtd_erros == 3
