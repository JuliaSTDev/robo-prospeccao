"""Descobre o site provável de uma empresa a partir do e-mail cadastral."""

LIVRES = {
    "gmail.com", "hotmail.com", "hotmail.com.br", "outlook.com", "outlook.com.br",
    "yahoo.com", "yahoo.com.br", "uol.com.br", "bol.com.br", "icloud.com",
    "live.com", "terra.com.br", "ig.com.br", "msn.com", "globo.com",
}

CONTADORES = {
    "contabilizei.com.br", "escon.com.br", "aspiralcont.com.br", "fmcontabil.com.br",
    "zapcontabil.com.br", "fscontroller.com.br", "meirafernandes.com.br",
    "awcontabil.com.br", "realizecont.com.br", "gsagestao.com.br",
    "vivahcontabil.com.br", "contabilidadebraz.com.br", "cbbassessoria.com.br",
}

REDES = {
    "cna.com.br", "culturainglesasp.com.br", "culturainglesa.com.br", "wizard.com.br",
    "ewizard.com.br", "redballoon.com.br", "berlitz.com.br", "escolasfisk.com.br",
    "escolafisk.com.br", "somoseducacao.com.br", "wizardjabaquara.com.br",
}

IGNORADOS = {
    "studioarcari.com.br",   # estúdio de arquitetura
    "uniqueonline.com.br",   # colchões
    "contec.com.br",         # contabilidade
    "nethall.com.br",        # provedor de internet
    "pryorglobal.com",       # grupo estrangeiro
}

PALAVRAS_DE_CONTADOR = ("contab",)


def extrair_dominio(email: str) -> str:
    """'contato@escola.com.br' -> 'escola.com.br'."""
    return email.split("@")[1].lower()


def site_candidato(email: str | None) -> str | None:
    """Devolve 'https://dominio' ou None. Não acessa a internet."""
    if email is None:
        return None
    dominio = extrair_dominio(email)
    if dominio in LIVRES | CONTADORES | REDES | IGNORADOS:
        return None
    if any(palavra in dominio for palavra in PALAVRAS_DE_CONTADOR):
        return None
    return f"https://{dominio}"


if __name__ == "__main__":
    assert site_candidato("contato@escola.com.br") == "https://escola.com.br"
    assert site_candidato("maria@gmail.com") is None
    assert site_candidato("x@contabilidadeabc.com.br") is None
    assert site_candidato("x@nethall.com.br") is None
    assert site_candidato(None) is None
    print("Tudo certo")