from datetime import date
from pathlib import Path

import pandas as pd

from robo.limpeza import (
    NATUREZA_EMPRESARIO_INDIVIDUAL,
    deve_evitar_contato,
    padronizar_email,
    padronizar_telefone,
)
from robo.models import Lead

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


def _limpar(valor) -> str | None:
    """Devolve o texto sem espaços, ou None se estiver vazio."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def montar_cnpj(linha: pd.Series) -> str:
    """Junta as 3 partes do CNPJ em um texto de 14 dígitos."""
    return linha["cnpj_basico"] + linha["cnpj_ordem"] + linha["cnpj_dv"]


def converter_data(texto: str) -> date | None:
    """Converte 'AAAAMMDD' em date. Devolve None se vier vazio ou inválido."""
    if not isinstance(texto, str) or len(texto) != 8 or texto == "00000000":
        return None
    try:
        return date(int(texto[0:4]), int(texto[4:6]), int(texto[6:8]))
    except ValueError:
        return None


def linha_para_lead(linha: pd.Series) -> Lead:
    """Converte uma linha da tabela (já com dados da empresa) em um Lead."""
    ddd = _limpar(linha["ddd"]) or ""
    numero = _limpar(linha["telefone"]) or ""
    evitar = deve_evitar_contato(linha["razao_social"], linha["natureza_juridica"])

    return Lead(
        cnpj=montar_cnpj(linha),
        razao_social=linha["razao_social"],
        cnae=linha["cnae"],
        municipio=linha["municipio"],
        uf=linha["uf"],
        porte=linha["porte"],
        data_abertura=converter_data(linha["data_abertura"]),
        matriz_filial=linha["matriz_filial"],
        nome_fantasia=_limpar(linha["nome_fantasia"]),
        telefone=padronizar_telefone(ddd + numero),
        email=padronizar_email(_limpar(linha["email"])),
        status="evitar_contato" if evitar else "novo",
    )


def coletar(cnae: str, municipio: str, pasta: str = "data") -> list[Lead]:
    """Coleta leads do nicho/cidade na base da Receita, sem empresário individual."""
    arquivos_estab = sorted(Path(pasta).glob("Estabelecimentos*.zip"))
    arquivos_emp = sorted(Path(pasta).glob("Empresas*.zip"))
    if not arquivos_estab or not arquivos_emp:
        raise FileNotFoundError(f"Não achei os arquivos da Receita em '{pasta}/'")

    partes = [filtrar_estabelecimentos(str(a), cnae, municipio) for a in arquivos_estab]
    estabelecimentos = pd.concat(partes, ignore_index=True)

    empresas = buscar_empresas(
        [str(a) for a in arquivos_emp], set(estabelecimentos["cnpj_basico"])
    )

    juntas = estabelecimentos.merge(empresas, on="cnpj_basico", how="inner")
    sem_individual = juntas[juntas["natureza_juridica"] != NATUREZA_EMPRESARIO_INDIVIDUAL]

    return [linha_para_lead(linha) for _, linha in sem_individual.iterrows()]


if __name__ == "__main__":
    leads = coletar(cnae="8593700", municipio="7107")
    evitar = sum(1 for lead in leads if lead.status == "evitar_contato")
    com_telefone = sum(1 for lead in leads if lead.telefone)
    com_email = sum(1 for lead in leads if lead.email)
    print(f"Leads coletados: {len(leads)}")
    print(f"Evitar contato (CPF no nome): {evitar}")
    print(f"Com telefone: {com_telefone} | Com e-mail: {com_email}")