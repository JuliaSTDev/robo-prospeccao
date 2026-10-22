"""Confere se o site aberto é mesmo da empresa e do nicho (regras, sem IA)."""
import re
import unicodedata
from urllib.parse import urlparse

PALAVRAS_NICHO = {
    "educacao": ["idioma", "ingles", "espanhol", "frances", "alemao", "curso", "aula",
                 "matricula", "escola", "english", "language", "professor", "turma",
                 "aprenda", "fluencia", "conversacao", "intercambio"],
    "estetica": ["estetica", "clinica", "procedimento", "harmonizacao", "depilacao",
                 "limpeza de pele", "botox", "laser", "tratamento", "agende"],
}

# palavras que não identificam a empresa (genéricas ou do nicho)
GENERICAS = {
    "de", "da", "do", "das", "dos", "e", "ltda", "me", "epp", "eireli", "sa",
    "escola", "escolas", "curso", "cursos", "centro", "instituto", "comercio",
    "servicos", "ensino", "educacao", "educacional", "idioma", "idiomas", "ingles",
    "english", "language", "languages", "lingua", "linguas", "school", "academy",
    "estetica", "clinica", "beleza", "brasil", "sao", "paulo",
    "empresa", "nova", "novo", "global", "internacional", "international",
    "grupo", "rede", "plus", "master", "top", "prime", "smart", "center",
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texto.lower())


def _texto_visivel(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html or "")
    titulo = " ".join(re.findall(r"(?is)<title[^>]*>(.*?)</title>", html))
    metas = " ".join(re.findall(r'(?is)<meta[^>]+content="([^"]*)"', html))
    corpo = re.sub(r"<[^>]+>", " ", html)
    return _normalizar(f"{titulo} {metas} {corpo}")[:80_000]


def _tokens_marca(nome: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", _normalizar(nome))
            if len(t) > 2 and t not in GENERICAS]


def confere_site(html: str, nome: str, nicho: str, url: str = "") -> tuple[bool, str]:
    """Devolve (confere, motivo)."""
    pagina = _texto_visivel(html)
    marca = _tokens_marca(nome)
    dominio = _normalizar(urlparse(url).netloc.replace("www.", "")) if url else ""

    palavras_pagina = set(re.findall(r"[a-z0-9]+", pagina))
    palavras_dominio = set(re.findall(r"[a-z0-9]+", dominio))

    batidas = [t for t in marca if t in palavras_pagina]
    # no domínio a marca costuma vir colada ("lbenglish"), então ali vale pedaço
    batidas += [t for t in marca if len(t) >= 4 and any(t in d for d in palavras_dominio)]
    batidas = list(dict.fromkeys(batidas))  # remove repetidas
    acha_nome = bool(batidas)

    hits_nicho = sum(1 for p in PALAVRAS_NICHO.get(nicho, []) if p in pagina)

    if not marca:
        if hits_nicho >= 2:
            return True, "nome genérico, só nicho"
        return False, "nome genérico, revisar"
    if acha_nome and hits_nicho >= 2:
        return True, f"nome e nicho batem ({', '.join(batidas[:2])})"
    if acha_nome:
        return False, f"nome bate ({', '.join(batidas[:2])}), nicho não"
    if hits_nicho >= 3:
        return False, "nicho bate, nome não (revisar)"
    return False, "não confere"