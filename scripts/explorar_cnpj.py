# import pandas as pd

# # ARQUIVO = "data/Estabelecimentos0.zip"

# # df = pd.read_csv(
# #     ARQUIVO,
# #     sep=";",
# #     header=None,
# #     encoding="latin-1",
# #     dtype=str,
# #     nrows=5,
# # )

# # # print(df.shape)
# # # print(df.T)

# # municipios = pd.read_csv(
# #     "data/Municipios.zip",
# #     sep=";",
# #     header=None,
# #     encoding="latin-1",
# #     dtype=str,
# # )

# # # print(municipios.shape)
# # # print(municipios[municipios[1].str.contains("SAO PAULO", na=False)])

# # print(municipios[municipios[1] == "SUZANO"])

# # # Confirmar o CNAE de escola de idiomas
# # cnaes = pd.read_csv(
# #     "data/Cnaes.zip",
# #     sep=";",
# #     header=None,
# #     encoding="latin-1",
# #     dtype=str,
# # )
# # print(cnaes.shape)
# # print(cnaes[cnaes[0] == "8593700"])



# # import pandas as pd

# # # Colunas que interessam no arquivo Estabelecimentos (posição → nome)
# COLUNAS = {
#     0: "cnpj_basico",
#     1: "cnpj_ordem",
#     2: "cnpj_dv",
#     3: "matriz_filial",
#     4: "nome_fantasia",
#     5: "situacao",
#     10: "data_abertura",
#     11: "cnae",
#     19: "uf",
#     20: "municipio",
#     21: "ddd",
#     22: "telefone",
#     27: "email",
# }

# SITUACAO_ATIVA = "02"
# TAMANHO_PEDACO = 200_000







# def filtrar_estabelecimentos(caminho: str, cnae: str, municipio: str) -> pd.DataFrame:
#     """Lê o arquivo em pedaços e devolve só os estabelecimentos do nicho, ativos, na cidade."""
#     pedacos_filtrados = []

#     leitor = pd.read_csv(
#         caminho,
#         sep=";",
#         header=None,
#         encoding="latin-1",
#         dtype=str,
#         usecols=list(COLUNAS.keys()),
#         chunksize=TAMANHO_PEDACO,
#     )

#     for pedaco in leitor:
#         pedaco = pedaco.rename(columns=COLUNAS)

#         filtrado = pedaco[
#             (pedaco["situacao"] == SITUACAO_ATIVA)
#             & (pedaco["cnae"] == cnae)
#             & (pedaco["municipio"] == municipio)
#         ]
#         pedacos_filtrados.append(filtrado)

#     return pd.concat(pedacos_filtrados, ignore_index=True)

# # if __name__ == "__main__":
# #     escolas = filtrar_estabelecimentos("data/Estabelecimentos0.zip", cnae="8593700", municipio="7107")
# #     print(f"Encontradas: {len(escolas)}")
# #     print(escolas.head())



# # empresas = pd.read_csv(
# #     "data/Empresas1.zip",
# #     sep=";",
# #     header=None,
# #     encoding="latin-1",
# #     dtype=str,
# #     nrows=5,
# # )
# # print(empresas.shape)
# # print(empresas.T)

# # naturezas = pd.read_csv(
# #     "data/Naturezas.zip",
# #     sep=";",
# #     header=None,
# #     encoding="latin-1",
# #     dtype=str,
# # )
# # print(naturezas[naturezas[0].isin(["2135", "2062", "2305"])])

# COLUNAS_EMPRESAS = {
#     0: "cnpj_basico",
#     1: "razao_social",
#     2: "natureza_juridica",
#     4: "capital_social",
#     5: "porte",
# }

# NATUREZA_EMPRESARIO_INDIVIDUAL = "2135"


# def buscar_empresas(caminhos: list[str], cnpjs_basicos: set[str]) -> pd.DataFrame:
#     """Procura, nos arquivos Empresas, só os CNPJs básicos informados."""
#     encontrados = []

#     for caminho in caminhos:
#         leitor = pd.read_csv(
#             caminho,
#             sep=";",
#             header=None,
#             encoding="latin-1",
#             dtype=str,
#             usecols=list(COLUNAS_EMPRESAS.keys()),
#             chunksize=TAMANHO_PEDACO,
#         )
#         for pedaco in leitor:
#             pedaco = pedaco.rename(columns=COLUNAS_EMPRESAS)
#             encontrados.append(pedaco[pedaco["cnpj_basico"].isin(cnpjs_basicos)])

#     return pd.concat(encontrados, ignore_index=True)

# if __name__ == "__main__":
#     escolas = filtrar_estabelecimentos("data/Estabelecimentos0.zip", cnae="8593700", municipio="7107")
#     print(f"Escolas no filtro: {len(escolas)}")

#     cnpjs = set(escolas["cnpj_basico"])
#     empresas = buscar_empresas(["data/Empresas1.zip"], cnpjs)
#     print(f"Encontradas no Empresas1: {len(empresas)}")

#     juntas = escolas.merge(empresas, on="cnpj_basico", how="inner")
#     sem_individual = juntas[juntas["natureza_juridica"] != NATUREZA_EMPRESARIO_INDIVIDUAL]
#     print(f"Depois de excluir empresário individual: {len(sem_individual)}")

#     print(juntas["natureza_juridica"].value_counts())