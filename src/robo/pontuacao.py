from collections import Counter
from datetime import date

from robo.models import Lead

PESOS = {
    "meta_pixel": 3,
    "google_tag": 1,
    "whatsapp_no_site": 2,
    "sem_chat": 2,
    "filiais": 2,
    "sem_site": -3,
    "site_inacessivel": -2,
}

MOTIVOS = {
    "meta_pixel": "tem pixel",
    "google_tag": "tem Google Tag",
    "whatsapp_no_site": "WhatsApp no site",
    "sem_chat": "sem chat",
    "filiais": "tem filiais",
    "sem_site": "sem site",
    "site_inacessivel": "site fora do ar",
}

NOTA_MINIMA = 0
NOTA_MAXIMA = 10


def pontuar(sinais: set[str]) -> tuple[int, str]:
    """Recebe os sinais detectados e devolve (nota de 0 a 10, motivo)."""
    aplicados = [sinal for sinal in PESOS if sinal in sinais]
    total = sum(PESOS[sinal] for sinal in aplicados)
    nota = max(NOTA_MINIMA, min(NOTA_MAXIMA, total))
    motivo = ", ".join(MOTIVOS[sinal] for sinal in aplicados) or "sem sinais"
    return nota, motivo


def sinais_do_lead(lead: Lead, qtd_unidades: int) -> set[str]:
    """Sinais que já conseguimos tirar do lead, sem ler o site."""
    sinais = set()
    if lead.site is None:
        sinais.add("sem_site")
    if qtd_unidades > 1:
        sinais.add("filiais")
    return sinais


def pontuar_leads(leads: list[Lead]) -> None:
    """Preenche nota e motivo_da_nota de cada lead da lista."""
    unidades_por_empresa = Counter(lead.cnpj[:8] for lead in leads)
    for lead in leads:
        sinais = sinais_do_lead(lead, unidades_por_empresa[lead.cnpj[:8]])
        lead.nota, lead.motivo_da_nota = pontuar(sinais)


if __name__ == "__main__":
    assert pontuar({"meta_pixel", "sem_chat", "filiais"}) == (
        7,
        "tem pixel, sem chat, tem filiais",
    )
    assert pontuar({"sem_site"}) == (0, "sem site")
    assert pontuar(set()) == (0, "sem sinais")
    assert pontuar(
        {"meta_pixel", "google_tag", "whatsapp_no_site", "sem_chat", "filiais"}
    )[0] == 10
    assert pontuar(
        {"meta_pixel", "google_tag", "whatsapp_no_site", "sem_chat", "filiais", "sem_site"}
    )[0] == 7

    def lead_de_teste(cnpj: str, site: str | None) -> Lead:
        return Lead(
            cnpj=cnpj, razao_social="ESCOLA TESTE LTDA", cnae="8593700",
            municipio="7107", uf="SP", porte="03",
            data_abertura=date(2000, 1, 1), matriz_filial="1", site=site,
        )

    sozinha = lead_de_teste("11111111000101", None)
    rede_a = lead_de_teste("22222222000101", "https://a.com.br")
    rede_b = lead_de_teste("22222222000202", "https://a.com.br")
    pontuar_leads([sozinha, rede_a, rede_b])
    assert (sozinha.nota, sozinha.motivo_da_nota) == (0, "sem site")
    assert (rede_a.nota, rede_a.motivo_da_nota) == (2, "tem filiais")
    assert rede_b.nota == 2

    print("Tudo certo")