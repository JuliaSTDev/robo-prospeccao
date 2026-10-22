"""Conta de onde vêm os domínios de e-mail dos leads (sem acessar a internet).

Usa as MESMAS listas do enriquecedor, para a análise bater com o que o robô faz.
Pré-requisito: data/leads_idiomas_sp.csv (gerado por scripts/gerar_csv_leads.py).
"""
import pandas as pd

from robo.enriquecedores.site_do_email import CONTADORES, IGNORADOS, LIVRES, REDES

df = pd.read_csv("data/leads_idiomas_sp.csv", dtype=str)

# "abertura@contabilizei.com.br" -> "contabilizei.com.br"
df["dominio"] = df["email"].str.split("@").str[1].str.lower()

eh_contador = df["dominio"].isin(CONTADORES) | df["dominio"].str.contains("contab", na=False)
descartados = LIVRES | REDES | IGNORADOS

sem_email = df["dominio"].isna().sum()
livres = df["dominio"].isin(LIVRES).sum()
contador = eh_contador.sum()
redes = df["dominio"].isin(REDES).sum()
ignorados = df["dominio"].isin(IGNORADOS).sum()
proprios = (df["dominio"].notna() & ~df["dominio"].isin(descartados) & ~eh_contador).sum()

total = len(df)
print(f"Total de leads:      {total}")
print(f"Sem e-mail:          {sem_email} ({sem_email / total:.0%})")
print(f"E-mail gratuito:     {livres} ({livres / total:.0%})")
print(f"Contador:            {contador} ({contador / total:.0%})")
print(f"Rede de franquia:    {redes} ({redes / total:.0%})")
print(f"Ignorados (errados): {ignorados}")
print(f"Domínio próprio:     {proprios} ({proprios / total:.0%})")

print("\nDomínios mais frequentes:")
print(df["dominio"].value_counts().head(40))
