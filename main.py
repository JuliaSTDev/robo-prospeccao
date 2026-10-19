from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_do_email import site_candidato
from robo.exportadores.ficha import exportar_fichas, selecionar_top

leads = coletar(cnae="8593700", municipio="7107")

for lead in leads:
    lead.site = site_candidato(lead.email)

top = selecionar_top(leads, n=20)
exportar_fichas(top, "data/fichas_top20.md", cidade="São Paulo")
print(f"{len(leads)} leads coletados, {len(top)} fichas em data/fichas_top20.md")