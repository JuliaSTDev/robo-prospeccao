"""Manda uma mensagem de teste pelo Telegram, para conferir o token e o chat id do .env.

Uso (com o .venv ligado):
    python -X utf8 scripts/testar_telegram.py
"""
from robo.notificadores.telegram import criar_notificador

notificar = criar_notificador()
if notificar is None:
    raise SystemExit("Faltam TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env")

notificar("Teste do robô de prospecção: o Telegram está funcionando.")
print("Mensagem enviada. Confira o Telegram.")
