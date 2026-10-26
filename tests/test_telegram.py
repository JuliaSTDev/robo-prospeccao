"""Testes do aviso no Telegram. Nada é enviado de verdade: a rede é trocada por funções falsas."""
from datetime import datetime, timedelta

import pytest

from robo import pipeline
from robo.models import Execucao
from robo.notificadores import telegram
from robo.notificadores.telegram import criar_notificador, enviar, montar_resumo


def execucao_de_exemplo(**campos) -> Execucao:
    inicio = datetime(2026, 10, 23, 18, 0, 0)
    execucao = Execucao(data_inicio=inicio, qtd_leads=1682, qtd_erros=1, **campos)
    execucao.data_fim = inicio + timedelta(minutes=50, seconds=37)
    return execucao


# ---------- montar_resumo ----------

def test_resumo_tem_os_numeros_da_execucao(criar_lead):
    texto = montar_resumo(execucao_de_exemplo(), [criar_lead()])
    assert "1682 leads · 1 erros · duração 0:50:37" in texto


def test_resumo_lista_os_melhores_leads_novos_em_ordem_de_nota(criar_lead):
    leads = [
        criar_lead(cnpj="11111111000101", nome_fantasia="Escola Baixa", nota=2, motivo_da_nota="sem site"),
        criar_lead(cnpj="22222222000101", nome_fantasia="Escola Alta", nota=9, motivo_da_nota="tem pixel",
                   telefone="11999999999", site="https://alta.com.br"),
    ]
    texto = montar_resumo(execucao_de_exemplo(), leads)

    assert texto.index("Escola Alta") < texto.index("Escola Baixa")
    assert "1. Escola Alta — nota 9/10 (tem pixel)" in texto
    assert "11999999999 · https://alta.com.br" in texto


def test_resumo_ignora_leads_que_ja_foram_tratados(criar_lead):
    leads = [
        criar_lead(cnpj="11111111000101", nome_fantasia="Já Aprovada", nota=10, status="aprovado"),
        criar_lead(cnpj="22222222000101", nome_fantasia="Ainda Nova", nota=3),
    ]
    texto = montar_resumo(execucao_de_exemplo(), leads)
    assert "Ainda Nova" in texto and "Já Aprovada" not in texto


def test_resumo_respeita_a_quantidade_de_destaques(criar_lead):
    leads = [criar_lead(cnpj=f"{i:08d}000101", nota=i) for i in range(1, 9)]
    texto = montar_resumo(execucao_de_exemplo(), leads, destaques=3)
    assert "8 leads novos para revisar. Os 3 melhores:" in texto


def test_resumo_sem_leads_novos(criar_lead):
    texto = montar_resumo(execucao_de_exemplo(), [criar_lead(status="aprovado")])
    assert "Nenhum lead novo para revisar." in texto


def test_resumo_cabe_no_limite_do_telegram(criar_lead):
    leads = [criar_lead(cnpj=f"{i:08d}000101", nome_fantasia="X" * 500, motivo_da_nota="m" * 500) for i in range(20)]
    assert len(montar_resumo(execucao_de_exemplo(), leads, destaques=20)) <= 4096


# ---------- enviar / criar_notificador ----------

def test_enviar_manda_o_texto_para_o_chat_certo(monkeypatch):
    enviado = {}

    def post_falso(url, json, timeout):
        enviado.update(url=url, json=json)
        return RespostaOk()

    monkeypatch.setattr(telegram.requests, "post", post_falso)
    enviar("oi", token="123:ABC", chat_id="42")

    assert enviado["url"] == "https://api.telegram.org/bot123:ABC/sendMessage"
    assert enviado["json"]["chat_id"] == "42" and enviado["json"]["text"] == "oi"


class RespostaRuim:
    ok = False
    status_code = 401
    text = "Unauthorized"


class RespostaOk:
    ok = True


def test_erro_do_telegram_nao_vaza_o_token(monkeypatch):
    monkeypatch.setattr(telegram.time, "sleep", lambda s: None)
    monkeypatch.setattr(telegram.requests, "post", lambda *a, **k: RespostaRuim())

    with pytest.raises(RuntimeError) as erro:
        enviar("oi", token="123:SEGREDO", chat_id="42")
    assert "401" in str(erro.value) and "SEGREDO" not in str(erro.value)


def test_tenta_de_novo_e_consegue_na_segunda(monkeypatch):
    respostas = [RespostaRuim(), RespostaOk()]
    chamadas = []
    monkeypatch.setattr(telegram.time, "sleep", lambda s: None)

    def post_falso(*args, **kwargs):
        chamadas.append(1)
        return respostas[len(chamadas) - 1]

    monkeypatch.setattr(telegram.requests, "post", post_falso)
    enviar("oi", token="123:ABC", chat_id="42")      # não levanta erro

    assert len(chamadas) == 2


def test_desiste_depois_de_todas_as_tentativas(monkeypatch):
    chamadas = []
    monkeypatch.setattr(telegram.time, "sleep", lambda s: None)
    monkeypatch.setattr(telegram.requests, "post", lambda *a, **k: chamadas.append(1) or RespostaRuim())

    with pytest.raises(RuntimeError):
        enviar("oi", token="123:ABC", chat_id="42", tentativas=3)

    assert len(chamadas) == 3


def test_sem_configuracao_nao_ha_notificador(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)   # não lê o .env de verdade
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert criar_notificador() is None


def test_com_configuracao_devolve_uma_funcao(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    assert callable(criar_notificador())


# ---------- no pipeline ----------

def test_pipeline_envia_o_resumo_no_fim(monkeypatch, criar_lead, tmp_path):
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead(nome_fantasia="Escola Teste", nota=0)])
    mensagens = []

    pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), rapido=True, notificador=mensagens.append,
    )

    assert len(mensagens) == 1
    assert "Escola Teste" in mensagens[0]


def test_telegram_fora_do_ar_nao_derruba_o_robo(monkeypatch, criar_lead, tmp_path):
    monkeypatch.setattr(pipeline, "coletar", lambda cnae, municipio: [criar_lead()])

    def notificador_quebrado(texto):
        raise RuntimeError("Telegram fora do ar")

    execucao = pipeline.rodar(
        cnae="8593700", municipio="7107", nicho="educacao", cidade="São Paulo",
        saida=str(tmp_path / "fichas.md"), rapido=True, notificador=notificador_quebrado,
    )

    assert execucao.qtd_leads == 1                  # a execução terminou normalmente
    assert (tmp_path / "fichas.md").exists()
