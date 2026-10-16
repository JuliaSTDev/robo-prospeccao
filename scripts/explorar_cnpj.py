import pandas as pd

ARQUIVO = "data/Estabelecimentos0.zip"

df = pd.read_csv(
    ARQUIVO,
    sep=";",
    header=None,
    encoding="latin-1",
    dtype=str,
    nrows=5,
)

# print(df.shape)
# print(df.T)

municipios = pd.read_csv(
    "data/Municipios.zip",
    sep=";",
    header=None,
    encoding="latin-1",
    dtype=str,
)

# print(municipios.shape)
# print(municipios[municipios[1].str.contains("SAO PAULO", na=False)])

print(municipios[municipios[1] == "SUZANO"])

# Confirmar o CNAE de escola de idiomas
cnaes = pd.read_csv(
    "data/Cnaes.zip",
    sep=";",
    header=None,
    encoding="latin-1",
    dtype=str,
)
print(cnaes.shape)
print(cnaes[cnaes[0] == "8593700"])