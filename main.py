import sys

from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_do_email import site_candidato
from robo.enriquecedores.site_sinais import enriquecer_sinais
from robo.enriquecedores.verificar_site import verificar_sites
from robo.exportadores.ficha import exportar_fichas, selecionar_top
from robo.pontuacao import pontuar_leads

CNAE = "8593700"      # ensino de idiomas
MUNICIPIO = "7107"    # São Paulo (código da Receita)
NICHO = "educacao"
CIDADE = "São Paulo"

# Uso:
#   python -X utf8 main.py            # completo: verifica sites e lê sinais (demora)
#   python -X utf8 main.py --sem-ia   # completo, sem gastar cota de IA
#   python -X utf8 main.py --rapido   # sem verificar sites nem ler sinais
usar_ia = "--sem-ia" not in sys.argv
rapido = "--rapido" in sys.argv

leads = coletar(cnae=CNAE, municipio=MUNICIPIO)

for lead in leads:
    lead.site = site_candidato(lead.email)

if rapido:
    print("Modo rápido: sites NÃO verificados e sinais NÃO lidos.\n")
else:
    verificar_sites(leads, NICHO, usar_ia=usar_ia)
    print()
    enriquecer_sinais(leads)

pontuar_leads(leads)

top = selecionar_top(leads, n=20)
exportar_fichas(top, "data/fichas_top20.md", cidade=CIDADE)

com_sinais = sum(1 for lead in top if lead.sinais)
print(f"\n{len(leads)} leads coletados, {len(top)} fichas em data/fichas_top20.md")
print(f"{com_sinais} dos {len(top)} primeiros têm sinais registrados")