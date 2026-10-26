"""Ponto de entrada do robô: configura o log e chama o pipeline.

Uso:
    python -X utf8 main.py              # completo: verifica sites, lê sinais e guarda no Supabase
    python -X utf8 main.py --sem-ia     # completo, sem gastar cota de IA
    python -X utf8 main.py --rapido     # sem verificar sites nem ler sinais (não salva no banco)
    python -X utf8 main.py --do-banco   # pula a coleta: refaz a nota e as fichas com os leads já guardados
    python -X utf8 main.py --sem-banco  # roda sem o Supabase (nada é lido nem guardado)
    python -X utf8 main.py --sem-telegram  # roda sem mandar o resumo no Telegram
"""
import logging
import sys
from pathlib import Path

from robo.armazenamento import conectar
from robo.notificadores.telegram import criar_notificador
from robo.pipeline import rodar

CNAE = "8593700"      # ensino de idiomas
MUNICIPIO = "7107"    # São Paulo (código da Receita)
NICHO = "educacao"
CIDADE = "São Paulo"
SAIDA = "data/fichas_top20.md"

log = logging.getLogger("main")


def configurar_log() -> None:
    """Define o nível, o formato e o destino do log: tela e arquivo."""
    Path("data").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("data/robo.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    configurar_log()
    try:
        banco = None if "--sem-banco" in sys.argv else conectar()
        notificador = None if "--sem-telegram" in sys.argv else criar_notificador()
        rodar(
            cnae=CNAE, municipio=MUNICIPIO, nicho=NICHO, cidade=CIDADE, saida=SAIDA,
            usar_ia="--sem-ia" not in sys.argv, rapido="--rapido" in sys.argv,
            banco=banco, do_banco="--do-banco" in sys.argv, notificador=notificador,
        )
    except Exception:
        log.exception("Execução interrompida por um erro")
        sys.exit(1)


if __name__ == "__main__":
    main()
