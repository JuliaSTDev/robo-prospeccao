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
