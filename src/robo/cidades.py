"""Nome da cidade a partir do código do município da Receita."""

CIDADES = {"7107": "São Paulo", "7151": "Suzano"}


def nome_da_cidade(codigo: str) -> str:
    return CIDADES.get(codigo, f"município {codigo}")