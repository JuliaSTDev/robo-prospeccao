import pytest

from robo.limpeza import (
    deve_evitar_contato,
    eh_empresario_individual,
    padronizar_cep,
    padronizar_email,
    padronizar_telefone,
    tem_cpf_no_nome,
)


@pytest.mark.parametrize("entrada, esperado", [
    ("1156449748", "(11) 5644-9748"),        # fixo, só números
    ("11956449748", "(11) 95644-9748"),      # celular
    ("(11) 5644-9748", "(11) 5644-9748"),    # já formatado
    ("123", None),                           # curto demais
    (None, None),
    ("1100000000", None),                    # placeholder da Receita
    ("1199999999", None),                    # placeholder da Receita
])
def test_padronizar_telefone(entrada, esperado):
    assert padronizar_telefone(entrada) == esperado


@pytest.mark.parametrize("entrada, esperado", [
    ("01310100", "01310-100"),
    ("01310-100", "01310-100"),
    ("00000000", None),
    ("123", None),
    (None, None),
])
def test_padronizar_cep(entrada, esperado):
    assert padronizar_cep(entrada) == esperado


@pytest.mark.parametrize("entrada, esperado", [
    ("  Contato@Escola.COM.br ", "contato@escola.com.br"),
    ("sem-arroba.com", None),
    ("a@b", None),
    (None, None),
])
def test_padronizar_email(entrada, esperado):
    assert padronizar_email(entrada) == esperado


@pytest.mark.parametrize("natureza, esperado", [
    ("2135", True),    # empresário individual (inclui o MEI)
    ("2062", False),   # sociedade limitada
    (None, False),
])
def test_eh_empresario_individual(natureza, esperado):
    assert eh_empresario_individual(natureza) is esperado


@pytest.mark.parametrize("razao_social, esperado", [
    ("MARIA DA SILVA 12345678901", True),
    ("ESCOLA ACAO LTDA", False),
    ("ESCOLA 12 LTDA", False),
    (None, False),
])
def test_tem_cpf_no_nome(razao_social, esperado):
    assert tem_cpf_no_nome(razao_social) is esperado


@pytest.mark.parametrize("razao_social, natureza, esperado", [
    ("JOAO TESTE 12345678901", "2062", True),   # CPF no nome
    ("ESCOLA LTDA", "2135", True),              # empresário individual
    ("ESCOLA LTDA", "2062", False),
    (None, None, False),
])
def test_deve_evitar_contato(razao_social, natureza, esperado):
    assert deve_evitar_contato(razao_social, natureza) is esperado
