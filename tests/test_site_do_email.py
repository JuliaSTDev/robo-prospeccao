import pytest

from robo.enriquecedores.site_do_email import site_candidato


@pytest.mark.parametrize("email, esperado", [
    ("contato@escola.com.br", "https://escola.com.br"),
    ("Contato@Escola.COM.br", "https://escola.com.br"),   # domínio em minúsculo
    ("maria@gmail.com", None),                            # e-mail gratuito
    ("x@contabilidadeabc.com.br", None),                  # contador (palavra 'contab')
    ("x@nethall.com.br", None),                           # domínio da lista de ignorados
    (None, None),
])
def test_site_candidato(email, esperado):
    assert site_candidato(email) == esperado
