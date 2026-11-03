"""Testes da API. Nenhum teste acessa o Supabase: o banco é um BancoFalso (conftest.py)."""
import pytest
from fastapi.testclient import TestClient

from robo.api.app import app, obter_banco
from robo.armazenamento import lead_para_linha

CNPJ_A = "11111111000101"   # nota 3, novo
CNPJ_B = "22222222000101"   # nota 8, novo
CNPJ_C = "33333333000101"   # nota 5, aprovado


@pytest.fixture
def banco(criar_lead, criar_banco):
    """Banco falso com 3 leads."""
    linhas = []
    for cnpj, nota, status in [(CNPJ_A, 3, "novo"), (CNPJ_B, 8, "novo"), (CNPJ_C, 5, "aprovado")]:
        linha = lead_para_linha(criar_lead(cnpj=cnpj, nota=nota))
        linha["status"] = status      # o banco devolve o status; nós nunca o enviamos
        linhas.append(linha)
    return criar_banco({"leads": linhas})


@pytest.fixture
def cliente(banco):
    """Cliente de teste: fala com a API usando o banco falso, sem servidor e sem internet."""
    app.dependency_overrides[obter_banco] = lambda: banco
    yield TestClient(app)
    app.dependency_overrides.clear()     # desfaz a troca, para não vazar para outros testes


def test_saude(cliente):
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_listar_traz_a_maior_nota_primeiro(cliente):
    resposta = cliente.get("/leads")
    assert resposta.status_code == 200
    assert [lead["nota"] for lead in resposta.json()] == [8, 5, 3]


def test_listar_filtra_por_status(cliente):
    resposta = cliente.get("/leads", params={"status": "novo"})
    assert resposta.status_code == 200
    assert [lead["nota"] for lead in resposta.json()] == [8, 3]


def test_listar_respeita_o_limite(cliente):
    resposta = cliente.get("/leads", params={"limite": 1})
    assert [lead["nota"] for lead in resposta.json()] == [8]     # o único que vem é o de maior nota


@pytest.mark.parametrize("params", [{"limite": 0}, {"limite": 201}, {"status": "banana"}])
def test_listar_recusa_parametros_invalidos(cliente, params):
    assert cliente.get("/leads", params=params).status_code == 422


def test_mudar_status(cliente, banco):
    resposta = cliente.patch(f"/leads/{CNPJ_B}/status", json={"status": "descartado"})

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "descartado"
    status_por_cnpj = {linha["cnpj"]: linha["status"] for linha in banco.tabelas["leads"]}
    assert status_por_cnpj == {CNPJ_A: "novo", CNPJ_B: "descartado", CNPJ_C: "aprovado"}   # só o B mudou


def test_mudar_status_de_cnpj_inexistente_da_404(cliente):
    resposta = cliente.patch("/leads/99999999999999/status", json={"status": "aprovado"})
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Lead não encontrado"}


@pytest.mark.parametrize("cnpj", ["123", "abcdefghijklmn", "1111111100010"])
def test_cnpj_invalido_da_422(cliente, cnpj):
    """Curto, com letras e com 13 dígitos: nenhum tem exatamente 14 números."""
    assert cliente.patch(f"/leads/{cnpj}/status", json={"status": "novo"}).status_code == 422


def test_status_invalido_no_corpo_da_422(cliente):
    assert cliente.patch(f"/leads/{CNPJ_B}/status", json={"status": "banana"}).status_code == 422


def test_corpo_ausente_da_422(cliente):
    assert cliente.patch(f"/leads/{CNPJ_B}/status").status_code == 422


def test_banco_fora_do_ar_da_502():
    class BancoQuebrado:
        """Um banco que sempre falha, como o Supabase fora do ar."""
        def ler(self, *args, **kwargs):
            raise RuntimeError("Supabase respondeu 401: Invalid API key")

    app.dependency_overrides[obter_banco] = lambda: BancoQuebrado()
    try:
        resposta = TestClient(app).get("/leads")
    finally:
        app.dependency_overrides.clear()

    assert resposta.status_code == 502
    assert resposta.json() == {"detail": "Banco de dados indisponível"}


# ---------- ficha do lead e status "respondido" ----------

def test_ver_lead_devolve_a_ficha_completa(cliente):
    resposta = cliente.get(f"/leads/{CNPJ_B}")

    assert resposta.status_code == 200
    ficha = resposta.json()
    assert ficha["cnpj"] == CNPJ_B
    assert ficha["razao_social"] == "ESCOLA TESTE LTDA"
    assert ficha["cidade"] == "São Paulo"          # o código 7107 vira o nome
    assert list(ficha["links"]) == ["Google", "Instagram", "Reclame Aqui", "Meta Ad Library"]


def test_ver_lead_inexistente_da_404(cliente):
    resposta = cliente.get("/leads/99999999999999")
    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Lead não encontrado"}


def test_ver_lead_com_cnpj_invalido_da_422(cliente):
    assert cliente.get("/leads/123").status_code == 422


def test_mudar_status_para_respondido(cliente):
    resposta = cliente.patch(f"/leads/{CNPJ_B}/status", json={"status": "respondido"})
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "respondido"
