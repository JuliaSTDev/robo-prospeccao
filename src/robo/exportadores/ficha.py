from datetime import date
from pathlib import Path
import re
from urllib.parse import quote_plus

from robo.models import Lead


SUFIXOS_SOCIETARIOS = re.compile(r"\b(LTDA|ME|EPP|EIRELI|S/S|S/?A)\b\.?", re.IGNORECASE)

# Texto da ficha para cada situação do site (valores de Lead.site_situacao)
ROTULOS_SITE = {
    "confere": "confirmado",
    "revisar": "revisar à mão",
    "bloqueado": "bloqueia robô, abrir à mão",
    "nao_confere": "o domínio do e-mail é de outra empresa",
    "inacessivel": "fora do ar",
    "sem_site": "sem domínio próprio no e-mail",
}

# Sinais que aparecem na ficha, na ordem em que aparecem
ROTULOS_SINAIS = {
    "whatsapp_no_site": "WhatsApp",
    "instagram_no_site": "Instagram",
    "meta_pixel": "Meta Pixel",
    "google_tag": "Google Tag",
    "so_formulario": "só formulário",
    "sem_chat": "sem chat",
    "site_inacessivel": "site fora do ar",
}


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
    """Escolhe os n leads mais promissores: maior nota primeiro, com critérios de desempate."""
    candidatos = [lead for lead in leads if not fora_do_perfil(lead)]
    ordenados = sorted(
        uma_por_empresa(candidatos),
        key=lambda lead: (
            -lead.nota,
            lead.site is None,
            lead.telefone is None,
            lead.porte not in {"03", "05"},
            lead.data_abertura or date.max,
        ),
    )
    return ordenados[:n]


def descrever_site(lead: Lead) -> str:
    """Site do lead com a situação da verificação, para a ficha."""
    rotulo = ROTULOS_SITE.get(lead.site_situacao, "não verificado")
    if lead.site:
        return f"{lead.site} ({rotulo})"
    return f"não encontrado ({rotulo})"


def descrever_sinais(lead: Lead) -> str:
    """Sinais detectados no site, em texto. '—' quando não há nenhum."""
    partes = [rotulo for sinal, rotulo in ROTULOS_SINAIS.items() if sinal in lead.sinais]
    return ", ".join(partes) or "—"


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
        f"- **Site:** {descrever_site(lead)}",
        f"- **Sinais no site:** {descrever_sinais(lead)}",
        "",
        f"**Verificar:** {verificar}",
        "",
        f"**Nota: {lead.nota}/10** — {lead.motivo_da_nota}",
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

    lead_teste = Lead(
        cnpj="11111111000101", razao_social="ESCOLA TESTE LTDA", cnae="8593700",
        municipio="7107", uf="SP", porte="03", matriz_filial="1",
        data_abertura=date(2010, 1, 1), site="https://escola.com.br",
        site_situacao="confere", sinais={"whatsapp_no_site", "sem_chat"},
    )
    assert descrever_site(lead_teste) == "https://escola.com.br (confirmado)"
    assert descrever_sinais(lead_teste) == "WhatsApp, sem chat"

    sem_nada = Lead(
        cnpj="22222222000101", razao_social="OUTRA ESCOLA LTDA", cnae="8593700",
        municipio="7107", uf="SP", porte="03", matriz_filial="1",
        data_abertura=date(2010, 1, 1), site=None, site_situacao="sem_site",
    )
    assert descrever_site(sem_nada) == "não encontrado (sem domínio próprio no e-mail)"
    assert descrever_sinais(sem_nada) == "—"

    for nome, link in links.items():
        print(f"{nome}: {link}")
    print("Tudo certo")