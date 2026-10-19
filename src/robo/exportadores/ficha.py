from datetime import date
from pathlib import Path
import re
from urllib.parse import quote_plus

from robo.models import Lead


SUFIXOS_SOCIETARIOS = re.compile(r"\b(LTDA|ME|EPP|EIRELI|S/S|S/?A)\b\.?", re.IGNORECASE)

def nome_para_busca(lead: Lead) -> str:
    """Nome fantasia (ou razão social) sem 'LTDA', 'ME' etc., para buscar."""
    nome = lead.nome_fantasia or lead.razao_social
    nome = SUFIXOS_SOCIETARIOS.sub("", nome)
    return " ".join(nome.split()).strip(" .-")


def montar_links(nome: str, cidade: str) -> dict[str, str]:
    """Links de busca para verificar o lead à mão. Só monta endereços, não acessa nada."""
    termo = quote_plus(f"{nome} {cidade}")
    nome_url = quote_plus(nome)
    return {
        "Google": f"https://www.google.com/search?q={termo}",
        "Instagram": f"https://www.google.com/search?q=site%3Ainstagram.com+{termo}",
        "Reclame Aqui": f"https://www.google.com/search?q=site%3Areclameaqui.com.br+{termo}",
        "Meta Ad Library": (
            "https://www.facebook.com/ads/library/"
            f"?active_status=all&ad_type=all&country=BR&q={nome_url}"
            "&search_type=keyword_exact_phrase"
        ),
    }


def uma_por_empresa(leads: list[Lead]) -> list[Lead]:
    """Mantém um lead por empresa (CNPJ básico), preferindo a matriz."""
    por_empresa: dict[str, Lead] = {}
    for lead in leads:
        base = lead.cnpj[:8]
        atual = por_empresa.get(base)
        if atual is None or (lead.matriz_filial == "1" and atual.matriz_filial != "1"):
            por_empresa[base] = lead
    return list(por_empresa.values())


def fora_do_perfil(lead: Lead) -> bool:
    """Associações (ALUMNI, Cervantes...) não são o perfil de venda."""
    return lead.razao_social.upper().startswith("ASSOCIACAO")


def selecionar_top(leads: list[Lead], n: int = 20) -> list[Lead]:
    """Escolhe os n leads mais promissores. Critério provisório, até existir a nota."""
    candidatos = [lead for lead in leads if not fora_do_perfil(lead)]
    ordenados = sorted(
        uma_por_empresa(candidatos),
        key=lambda lead: (
            lead.site is None,
            lead.telefone is None,
            lead.porte not in {"03", "05"},
            lead.data_abertura or date.max,
        ),
    )
    return ordenados[:n]


def ficha_markdown(lead: Lead, cidade: str) -> str:
    """Monta a ficha de um lead em Markdown, com os links de verificação."""
    titulo = lead.nome_fantasia or lead.razao_social
    links = montar_links(nome_para_busca(lead), cidade)
    verificar = " · ".join(f"[{nome_link}]({url})" for nome_link, url in links.items())

    linhas = [
        f"## {titulo}",
        "",
        f"- **Razão social:** {lead.razao_social}",
        f"- **CNPJ:** {lead.cnpj}",
        f"- **Aberta em:** {lead.data_abertura}",
        f"- **Porte:** {lead.porte}",
        f"- **Telefone:** {lead.telefone or '—'}",
        f"- **E-mail:** {lead.email or '—'}",
        f"- **Site candidato (não verificado):** {lead.site or '—'}",
        "",
        f"**Verificar:** {verificar}",
        "",
    ]
    return "\n".join(linhas)


def exportar_fichas(leads: list[Lead], caminho: str, cidade: str) -> None:
    """Grava as fichas de todos os leads em um arquivo Markdown."""
    fichas = [ficha_markdown(lead, cidade) for lead in leads]
    texto = "# Fichas de prospecção\n\n" + "\n---\n\n".join(fichas)
    Path(caminho).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    links = montar_links("Escola Ação", "São Paulo")
    assert links["Google"] == (
        "https://www.google.com/search?q=Escola+A%C3%A7%C3%A3o+S%C3%A3o+Paulo"
    )
    for nome, link in links.items():
        print(f"{nome}: {link}")