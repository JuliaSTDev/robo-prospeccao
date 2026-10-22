"""Mede a hipótese da task: em quantos % dos leads conseguimos achar o site certo.

Roda em TODOS os leads do nicho/cidade (não só no top 20).
Uso:
    python -X utf8 scripts/medir_sites.py            # com IA nos casos duvidosos
    python -X utf8 scripts/medir_sites.py --sem-ia   # só regras (não gasta cota)
"""
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_do_email import site_candidato
from robo.enriquecedores.verificar_site import relatorio_sites, verificar_sites
from robo.exportadores.ficha import fora_do_perfil, uma_por_empresa

CNAE = "8593700"      # ensino de idiomas
MUNICIPIO = "7107"    # São Paulo (código da Receita)
NICHO = "educacao"
SAIDA = Path("data/sites_verificados.csv")

usar_ia = "--sem-ia" not in sys.argv

leads = coletar(cnae=CNAE, municipio=MUNICIPIO)
leads = [lead for lead in uma_por_empresa(leads) if not fora_do_perfil(lead)]
for lead in leads:
    lead.site = site_candidato(lead.email)

print(f"Verificando {len(leads)} empresas (IA {'ligada' if usar_ia else 'desligada'})...\n")
verificar_sites(leads, NICHO, usar_ia=usar_ia)

# todo lead precisa sair da verificação com um veredito
sem_veredito = [lead for lead in leads if not lead.site_situacao]
assert not sem_veredito, f"{len(sem_veredito)} leads ficaram sem site_situacao"

print("\n" + relatorio_sites(leads))

colunas = ["cnpj", "razao_social", "nome_fantasia", "email", "site", "site_situacao", "site_motivo"]
pd.DataFrame([asdict(lead) for lead in leads])[colunas].to_csv(SAIDA, index=False, encoding="utf-8")
print(f"\nDetalhe por empresa salvo em {SAIDA}")