"""Testes do pipeline. A coleta e as etapas lentas são trocadas por funções falsas."""
from collections import Counter

import pytest

from robo import pipeline
from robo.armazenamento import lead_para_linha


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


# ---------- banco (Supabase) ----------

def tabelas_enviadas(banco):
    return [tabela for tabela, _, _ in banco.envios]


def test_execucao_completa_salva_leads_e_execucao_no_banco(monkeypatch, criar_lead, criar_banco, tmp_path):
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead(email="contato@escola.com.br")])
    monkeypatch.setattr(pipeline, "verificar_sites", lambda leads, nicho, usar_ia: Counter())
    monkeypatch.setattr(pipeline, "enriquecer_sinais", lambda leads: Counter())
    banco = criar_banco()

    pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), usar_ia=False, banco=banco,
    )

    assert tabelas_enviadas(banco) == ["leads", "execucoes"]


def test_modo_rapido_nao_salva_leads_mas_registra_a_execucao(monkeypatch, criar_lead, criar_banco, tmp_path):
    """Salvar sites não verificados apagaria o que já foi verificado antes."""
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead()])
    banco = criar_banco()

    pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), rapido=True, banco=banco,
    )

    assert tabelas_enviadas(banco) == ["execucoes"]


def test_do_banco_pula_a_coleta_e_filtra_cnae_e_municipio(monkeypatch, criar_lead, criar_banco, tmp_path):
    def coleta_proibida(cnae, municipio):
        raise AssertionError("não era para coletar de novo")

    monkeypatch.setattr(pipeline, "coletar", coleta_proibida)
    linhas = []
    for lead in [
        criar_lead(cnpj="11111111000101"),
        criar_lead(cnpj="22222222000101", cnae="9999999"),      # outro CNAE: fica de fora
        criar_lead(cnpj="33333333000101", municipio="1111"),    # outro município: fica de fora
    ]:
        linha = lead_para_linha(lead)
        linha["status"] = "novo"
        linhas.append(linha)
    banco = criar_banco({"leads": linhas})

    execucao = pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), banco=banco, do_banco=True,
    )

    assert execucao.qtd_leads == 1
    assert execucao.parametros["do_banco"] == "True"
    assert (tmp_path / "fichas.md").exists()


def test_do_banco_sem_banco_e_erro_claro(tmp_path):
    with pytest.raises(ValueError):
        pipeline.rodar(
            cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
            saida=str(tmp_path / "fichas.md"), do_banco=True,
        )


def test_banco_fora_do_ar_nao_impede_as_fichas(monkeypatch, criar_lead, tmp_path):
    class BancoQueQuebra:
        def ler(self, tabela, ordem, inicio, quantidade):
            return []                                   # a conexão inicial funciona...

        def enviar(self, tabela, linhas, chave_unica):  # ...mas gravar falha
            raise RuntimeError("Supabase fora do ar")

    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead()])
    monkeypatch.setattr(pipeline, "verificar_sites", lambda leads, nicho, usar_ia: Counter())
    monkeypatch.setattr(pipeline, "enriquecer_sinais", lambda leads: Counter())
    saida = tmp_path / "fichas.md"

    execucao = pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(saida), usar_ia=False, banco=BancoQueQuebra(),
    )

    assert saida.exists()          # a ficha saiu mesmo assim
    assert execucao.qtd_erros == 1  # e o erro foi contado


def test_conexao_ruim_falha_antes_de_coletar(monkeypatch, tmp_path):
    """Chave ou URL erradas têm que aparecer em 1 segundo, não depois de 50 minutos."""
    class BancoSemConexao:
        def ler(self, tabela, ordem, inicio, quantidade):
            raise RuntimeError("Supabase respondeu 404")

    def coleta_proibida(cnae, municipio):
        raise AssertionError("não era para coletar: a conexão já tinha falhado")

    monkeypatch.setattr(pipeline, "coletar", coleta_proibida)

    with pytest.raises(RuntimeError, match="404"):
        pipeline.rodar(
            cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
            saida=str(tmp_path / "fichas.md"), banco=BancoSemConexao(),
        )
