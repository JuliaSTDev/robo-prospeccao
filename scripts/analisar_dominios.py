import pandas as pd
from robo.enriquecedores.site_do_email import LIVRES, CONTADORES, REDES

# Provedores de e-mail gratuito: não levam a nenhum site
LIVRES = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.br",
    "uol.com.br", "bol.com.br", "icloud.com", "live.com", "terra.com.br",
    "ig.com.br", "msn.com",
}

df = pd.read_csv("data/leads_idiomas_sp.csv", dtype=str)

# "abertura@contabilizei.com.br" -> "contabilizei.com.br"
df["dominio"] = df["email"].str.split("@").str[1]

contagem = df["dominio"].value_counts()

# Provedores de e-mail gratuito: não levam a nenhum site
LIVRES = {
    "gmail.com", "hotmail.com", "outlook.com", "outlook.com.br", "yahoo.com",
    "yahoo.com.br", "uol.com.br", "bol.com.br", "icloud.com", "live.com",
    "terra.com.br", "ig.com.br", "msn.com", "globo.com",
}

CONTADORES = {
    "contabilizei.com.br", "escon.com.br", "aspiralcont.com.br",
    "fmcontabil.com.br", "zapcontabil.com.br", "fscontroller.com.br",
    "meirafernandes.com.br",
}

REDES = {
    "cna.com.br", "culturainglesasp.com.br", "culturainglesa.com.br",
    "wizard.com.br", "ewizard.com.br", "redballoon.com.br", "berlitz.com.br",
    "escolasfisk.com.br", "escolafisk.com.br", "somoseducacao.com.br",
}
df = pd.read_csv("data/leads_idiomas_sp.csv", dtype=str)

# "abertura@contabilizei.com.br" -> "contabilizei.com.br"
df["dominio"] = df["email"].str.split("@").str[1]

contagem = df["dominio"].value_counts()

sem_email = df["dominio"].isna().sum()
livres = df["dominio"].isin(LIVRES).sum()
contador = df["dominio"].isin(CONTADORES).sum()
redes = df["dominio"].isin(REDES).sum()
proprios = (
    df["dominio"].notna()
    & ~df["dominio"].isin(LIVRES | CONTADORES | REDES)
).sum()

print(f"Total de leads:      {len(df)}")
print(f"Sem e-mail:          {sem_email}")
print(f"E-mail gratuito:     {livres}")
print(f"Contador:            {contador}")
print(f"Rede de franquia:    {redes}")
print(f"Domínio próprio:     {proprios}")

print()
print(contagem.head(40))