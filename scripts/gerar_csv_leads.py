from dataclasses import asdict

import pandas as pd

from robo.coletores.cnpj_receita import coletar

leads = coletar(cnae="8593700", municipio="7107")

df = pd.DataFrame([asdict(lead) for lead in leads])
df.to_csv("data/leads_idiomas_sp.csv", index=False)
print(f"{len(df)} leads salvos")