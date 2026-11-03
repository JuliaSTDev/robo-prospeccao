"""Peças compartilhadas pelos testes (o pytest carrega este arquivo sozinho)."""
from datetime import date

import pytest

from robo.models import Lead


@pytest.fixture
def criar_lead():
    """Devolve uma função que cria leads de teste. Passe só o que quiser mudar."""

    def _criar(**campos) -> Lead:
        base = dict(
            cnpj="11111111000101", razao_social="ESCOLA TESTE LTDA", cnae="8593700",
            municipio="7107", uf="SP", porte="03", matriz_filial="1",
            data_abertura=date(2010, 1, 1),
        )
        base.update(campos)
        return Lead(**base)

    return _criar


class BancoFalso:
    """Imita o Banco do Supabase na memória: guarda o que é enviado e devolve o que for combinado."""

    def __init__(self, tabelas: dict[str, list[dict]] | None = None):
        self.envios: list[tuple[str, list[dict], str]] = []        # (tabela, linhas, chave_unica)
        self.leituras: list[tuple[int, int]] = []                  # (inicio, quantidade)
        self.atualizacoes: list[tuple[str, dict, dict]] = []       # (tabela, filtros, valores)
        self.tabelas = tabelas or {}

    def enviar(self, tabela, linhas, chave_unica):
        self.envios.append((tabela, linhas, chave_unica))

    def ler(self, tabela, ordem, inicio, quantidade, filtros=None, descendente=False):
        self.leituras.append((inicio, quantidade))
        linhas = self.tabelas.get(tabela, [])
        for coluna, valor in (filtros or {}).items():
            # na URL tudo é texto ("eq.8"), então o falso também compara como texto
            linhas = [linha for linha in linhas if str(linha.get(coluna)) == str(valor)]
        if descendente:   # igual ao banco: valor maior primeiro, CNPJ desempata
            linhas = sorted(linhas, key=lambda linha: (-linha[ordem], linha["cnpj"]))
        else:
            linhas = sorted(linhas, key=lambda linha: linha[ordem])
        return linhas[inicio:inicio + quantidade]

    def atualizar(self, tabela, filtros, valores):
        self.atualizacoes.append((tabela, filtros, valores))
        atualizadas = []
        for linha in self.tabelas.get(tabela, []):
            if all(str(linha.get(coluna)) == str(valor) for coluna, valor in filtros.items()):
                linha.update(valores)
                atualizadas.append(linha)
        return atualizadas


@pytest.fixture
def criar_banco():
    """Devolve a classe BancoFalso: criar_banco() ou criar_banco({"leads": [linhas...]})."""
    return BancoFalso
