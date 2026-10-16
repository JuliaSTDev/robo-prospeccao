import pandas as pd

# Colunas que interessam no arquivo Estabelecimentos (posição → nome)
COLUNAS = {
    0: "cnpj_basico",
    1: "cnpj_ordem",
    2: "cnpj_dv",
    3: "matriz_filial",
    4: "nome_fantasia",
    5: "situacao",
    10: "data_abertura",
    11: "cnae",
    19: "uf",
    20: "municipio",
    21: "ddd",
    22: "telefone",
    27: "email",
}

# Colunas que interessam no arquivo Empresas (posição → nome)
COLUNAS_EMPRESAS = {
    0: "cnpj_basico",
    1: "razao_social",
    2: "natureza_juridica",
    4: "capital_social",
    5: "porte",
}

SITUACAO_ATIVA = "02"
NATUREZA_EMPRESARIO_INDIVIDUAL = "2135"
TAMANHO_PEDACO = 200_000


def filtrar_estabelecimentos(caminho: str, cnae: str, municipio: str) -> pd.DataFrame:
    """Lê o arquivo em pedaços e devolve só os estabelecimentos do nicho, ativos, na cidade."""
    pedacos_filtrados = []

    leitor = pd.read_csv(
        caminho,
        sep=";",
        header=None,
        encoding="latin-1",
        dtype=str,
        usecols=list(COLUNAS.keys()),
        chunksize=TAMANHO_PEDACO,
    )

    for pedaco in leitor:
        pedaco = pedaco.rename(columns=COLUNAS)

        filtrado = pedaco[
            (pedaco["situacao"] == SITUACAO_ATIVA)
            & (pedaco["cnae"] == cnae)
            & (pedaco["municipio"] == municipio)
        ]
        pedacos_filtrados.append(filtrado)

    return pd.concat(pedacos_filtrados, ignore_index=True)


def buscar_empresas(caminhos: list[str], cnpjs_basicos: set[str]) -> pd.DataFrame:
    """Procura, nos arquivos Empresas, só os CNPJs básicos informados."""
    encontrados = []

    for caminho in caminhos:
        leitor = pd.read_csv(
            caminho,
            sep=";",
            header=None,
            encoding="latin-1",
            dtype=str,
            usecols=list(COLUNAS_EMPRESAS.keys()),
            chunksize=TAMANHO_PEDACO,
        )
        for pedaco in leitor:
            pedaco = pedaco.rename(columns=COLUNAS_EMPRESAS)
            encontrados.append(pedaco[pedaco["cnpj_basico"].isin(cnpjs_basicos)])

    return pd.concat(encontrados, ignore_index=True)


if __name__ == "__main__":
    from pathlib import Path

    # Path("data").glob("Estabelecimentos*.zip") acha todos os arquivos que
    # combinam com o padrão; sorted() deixa em ordem (0, 1, 2...)
    arquivos_estab = sorted(Path("data").glob("Estabelecimentos*.zip"))
    arquivos_emp = sorted(Path("data").glob("Empresas*.zip"))
    print(f"Arquivos: {len(arquivos_estab)} Estabelecimentos, {len(arquivos_emp)} Empresas")

    # 1) filtra cada arquivo de Estabelecimentos e junta tudo
    partes = []
    for arquivo in arquivos_estab:
        parte = filtrar_estabelecimentos(str(arquivo), cnae="8593700", municipio="7107")
        print(f"  {arquivo.name}: {len(parte)}")
        partes.append(parte)
    escolas = pd.concat(partes, ignore_index=True)
    print(f"Escolas no filtro: {len(escolas)}")

    # 2) busca a empresa de cada uma em TODOS os arquivos de Empresas
    cnpjs = set(escolas["cnpj_basico"])
    empresas = buscar_empresas([str(a) for a in arquivos_emp], cnpjs)
    print(f"Empresas encontradas: {len(empresas)}")

    # 3) junta e tira empresário individual
    juntas = escolas.merge(empresas, on="cnpj_basico", how="inner")
    sem_individual = juntas[juntas["natureza_juridica"] != NATUREZA_EMPRESARIO_INDIVIDUAL]
    print(f"Depois de excluir empresário individual: {len(sem_individual)}")

    print(juntas["natureza_juridica"].value_counts())
    