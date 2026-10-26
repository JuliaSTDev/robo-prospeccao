"""Avisos no Telegram: resumo da execução com os melhores leads novos.

montar_resumo() só monta o texto (nos testes não precisa de internet).
enviar() fala com a API do Telegram. criar_notificador() lê o token e o chat do .env.
"""
import logging
import os
import time
from typing import Callable

import requests

from robo.exportadores.ficha import selecionar_top
from robo.models import Execucao, Lead

log = logging.getLogger(__name__)

LIMITE_TELEGRAM = 4096   # tamanho máximo de uma mensagem


def montar_resumo(execucao: Execucao, leads: list[Lead], destaques: int = 5) -> str:
    """Texto do aviso: números da execução + os melhores leads que ainda estão com status 'novo'."""
    fim = execucao.data_fim or execucao.data_inicio
    duracao = str(fim - execucao.data_inicio).split(".")[0]
    linhas = [
        f"Robô de prospecção — execução {execucao.id[:8]}",
        f"{execucao.qtd_leads} leads · {execucao.qtd_erros} erros · duração {duracao}",
        "",
    ]

    novos = [lead for lead in leads if lead.status == "novo"]
    top = selecionar_top(novos, n=destaques)
    if not top:
        linhas.append("Nenhum lead novo para revisar.")
    else:
        linhas.append(f"{len(novos)} leads novos para revisar. Os {len(top)} melhores:")
        for posicao, lead in enumerate(top, start=1):
            nome = lead.nome_fantasia or lead.razao_social
            linhas.append(f"{posicao}. {nome} — nota {lead.nota}/10 ({lead.motivo_da_nota})")
            contato = [parte for parte in (lead.telefone, lead.site) if parte]
            if contato:
                linhas.append("   " + " · ".join(contato))

    return "\n".join(linhas)[:LIMITE_TELEGRAM]


def _enviar_uma_vez(texto: str, token: str, chat_id: str) -> None:
    """Uma tentativa. Texto puro (sem Markdown), para nomes com _ ou * não quebrarem."""
    resposta = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": texto, "disable_web_page_preview": True},
        timeout=30,
    )
    if not resposta.ok:
        # não repete a URL no erro: ela contém o token
        raise RuntimeError(f"Telegram respondeu {resposta.status_code}: {resposta.text[:200]}")


def enviar(texto: str, token: str, chat_id: str, tentativas: int = 3, pausa: float = 2.0) -> None:
    """Manda a mensagem; se falhar, espera e tenta de novo. Na última falha, levanta o erro."""
    for tentativa in range(1, tentativas + 1):
        try:
            _enviar_uma_vez(texto, token, chat_id)
            return
        except Exception as erro:   # rede caiu, Telegram instável, chave errada...
            log.warning("Envio ao Telegram falhou (tentativa %d de %d): %s", tentativa, tentativas, erro)
            if tentativa == tentativas:
                raise
            time.sleep(pausa)


def criar_notificador() -> Callable[[str], None] | None:
    """Devolve uma função que envia texto, ou None se o Telegram não estiver configurado no .env."""
    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("Telegram não configurado (faltam TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env): sem aviso")
        return None
    return lambda texto: enviar(texto, token, chat_id)
