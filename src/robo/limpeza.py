import re


def so_digitos(texto: str | None) -> str:
    """Tira tudo que não é número. '(11) 5644-9748' -> '1156449748'."""
    return re.sub(r"\D", "", texto or "")


def padronizar_telefone(telefone: str | None) -> str | None:
    """Devolve '(11) 5644-9748' ou '(11) 95644-9748'. Inválido vira None."""
    digitos = so_digitos(telefone)
    if len(digitos) not in (10, 11):
        return None
    numero = digitos[2:]
    if len(set(numero)) == 1 or numero.count("0") >= 6:
        return None  # placeholder da Receita: 00000000, 99999999...
    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"

PADRAO_EMAIL = re.compile(r"^[^@\s]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
NATUREZA_EMPRESARIO_INDIVIDUAL = "2135"
PADRAO_CPF_NO_NOME = re.compile(r"\d{11}$")

def padronizar_cep(cep: str | None) -> str | None:
    """Devolve 'XXXXX-XXX'. CEP inválido ou zerado vira None."""
    digitos = so_digitos(cep)
    if len(digitos) != 8 or digitos == "00000000":
        return None
    return f"{digitos[:5]}-{digitos[5:]}"


def padronizar_email(email: str | None) -> str | None:
    """Devolve o e-mail em minúsculo, ou None se for inválido."""
    if email is None:
        return None
    email = email.strip().lower()
    if PADRAO_EMAIL.match(email):
        return email
    return None

def eh_empresario_individual(natureza: str | None) -> bool:
    """Natureza jurídica 2135: empresário individual (inclui o MEI)."""
    return natureza == NATUREZA_EMPRESARIO_INDIVIDUAL


def tem_cpf_no_nome(razao_social: str | None) -> bool:
    """'MARIA DA SILVA 12345678901' -> True. Sinal de pessoa física."""
    texto = (razao_social or "").strip()
    return bool(PADRAO_CPF_NO_NOME.search(texto))


def deve_evitar_contato(razao_social: str | None, natureza: str | None) -> bool:
    """True para MEI e empresário individual (LGPD: não abordar direto)."""
    return eh_empresario_individual(natureza) or tem_cpf_no_nome(razao_social)



if __name__ == "__main__":
    assert padronizar_telefone("1156449748") == "(11) 5644-9748"
    assert padronizar_telefone("11956449748") == "(11) 95644-9748"
    assert padronizar_telefone("(11) 5644-9748") == "(11) 5644-9748"
    assert padronizar_telefone("123") is None
    assert padronizar_telefone(None) is None
    assert padronizar_cep("01310100") == "01310-100"
    assert padronizar_cep("01310-100") == "01310-100"
    assert padronizar_cep("00000000") is None
    assert padronizar_cep("123") is None
    assert padronizar_email("  Contato@Escola.COM.br ") == "contato@escola.com.br"
    assert padronizar_email("sem-arroba.com") is None
    assert padronizar_email("a@b") is None
    assert padronizar_email(None) is None
    assert eh_empresario_individual("2135") is True
    assert eh_empresario_individual("2062") is False
    assert eh_empresario_individual(None) is False
    assert tem_cpf_no_nome("MARIA DA SILVA 12345678901") is True
    assert tem_cpf_no_nome("ESCOLA ACAO LTDA") is False
    assert tem_cpf_no_nome("ESCOLA 12 LTDA") is False
    assert deve_evitar_contato("JOAO TESTE 12345678901", "2062") is True
    assert deve_evitar_contato("ESCOLA LTDA", "2135") is True
    assert deve_evitar_contato("ESCOLA LTDA", "2062") is False
    assert deve_evitar_contato(None, None) is False
    assert padronizar_telefone("1100000000") is None
    assert padronizar_telefone("1199999999") is None
    print("Tudo certo")