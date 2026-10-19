# Provedores de e-mail gratuito: não levam a nenhum site
LIVRES = {
    "gmail.com", "hotmail.com", "outlook.com", "outlook.com.br", "yahoo.com",
    "yahoo.com.br", "uol.com.br", "bol.com.br", "icloud.com", "live.com",
    "terra.com.br", "ig.com.br", "msn.com", "globo.com",
}

# E-mail do escritório de contabilidade, não da escola
CONTADORES = {
    "contabilizei.com.br", "escon.com.br", "aspiralcont.com.br",
    "fmcontabil.com.br", "zapcontabil.com.br", "fscontroller.com.br",
    "meirafernandes.com.br",
}

# Redes de franquia: o site é da marca, não da unidade
REDES = {
    "cna.com.br", "culturainglesasp.com.br", "culturainglesa.com.br",
    "wizard.com.br", "ewizard.com.br", "redballoon.com.br", "berlitz.com.br",
    "escolasfisk.com.br", "escolafisk.com.br", "somoseducacao.com.br",
}


def extrair_dominio(email: str | None) -> str | None:
    """'Contato@Escola.com.br' -> 'escola.com.br'. None se não houver e-mail válido."""
    if not email or "@" not in email:
        return None
    return email.split("@")[1].strip().lower()


def site_candidato(email: str | None) -> str | None:
    """Devolve o endereço provável do site da escola, ou None se o e-mail não ajuda."""
    dominio = extrair_dominio(email)
    if dominio is None:
        return None
    if dominio in LIVRES or dominio in CONTADORES or dominio in REDES:
        return None
    return f"https://{dominio}"


if __name__ == "__main__":
    assert site_candidato("abertura@contabilizei.com.br") is None
    assert site_candidato("fulano@gmail.com") is None
    assert site_candidato("contato@wizard.com.br") is None
    assert site_candidato(None) is None
    assert site_candidato("Contato@TimesIdiomas.com.br") == "https://timesidiomas.com.br"
    print("Tudo certo")