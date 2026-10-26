"""Orquestra o robô: coletar -> enriquecer -> pontuar -> guardar no banco -> exportar as fichas.

Se uma peça falhar em UM lead, o erro vai para o log e o pipeline segue com os outros.
Cada execução é descrita por uma Execucao (início, fim, quantos leads, quantos erros).

O banco (Supabase) é opcional: sem ele o robô roda igual, só não guarda nada.
Com do_banco=True o robô pula a coleta lenta e trabalha com os leads já guardados.
O notificador (Telegram) também é opcional: é uma função que recebe o texto do resumo e o envia.
"""
import logging
from datetime import date, datetime

from robo.armazenamento import carregar_leads, salvar_execucao, salvar_leads, verificar_conexao
from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_do_email import site_candidato
from robo.enriquecedores.site_sinais import enriquecer_sinais
from robo.enriquecedores.verificar_site import verificar_sites
from robo.exportadores.ficha import exportar_fichas, selecionar_top
from robo.models import Execucao, Lead
from robo.notificadores.telegram import montar_resumo
from robo.pontuacao import pontuar_leads

log = logging.getLogger(__name__)


def definir_sites_candidatos(leads: list[Lead]) -> int:
    """Preenche lead.site a partir do e-mail. Devolve quantos leads deram erro."""
    erros = 0
    for lead in leads:
        try:
            lead.site = site_candidato(lead.email)
        except Exception:
            log.exception("Falha ao achar o site candidato do lead %s", lead.cnpj[:8])
            erros += 1
    return erros


def guardar_leads(leads: list[Lead], banco) -> int:
    """Salva no banco sem derrubar o robô. Devolve 1 se deu erro, 0 se deu certo."""
    try:
        salvar_leads(leads, banco)
        return 0
    except Exception:
        log.exception("Falha ao salvar os leads no banco (as fichas continuam sendo geradas)")
        return 1


def rodar(cnae: str, municipio: str, nicho: str, cidade: str, saida: str,
          usar_ia: bool = True, rapido: bool = False, qtd_fichas: int = 20,
          banco=None, do_banco: bool = False, notificador=None) -> Execucao:
    """Roda o robô de ponta a ponta e devolve o registro da execução."""
    if do_banco and banco is None:
        raise ValueError("do_banco=True precisa de um banco conectado")

    if banco is not None:
        verificar_conexao(banco)   # falha já, antes de coletar e verificar sites (a execução completa é longa)

    execucao = Execucao(parametros={
        "cnae": cnae, "municipio": municipio, "nicho": nicho,
        "ia": str(usar_ia), "rapido": str(rapido), "do_banco": str(do_banco),
    })
    log.info("Execução %s iniciada: %s", execucao.id[:8], execucao.parametros)

    leads: list[Lead] = []
    try:
        if do_banco:
            todos = carregar_leads(banco)
            leads = [lead for lead in todos if lead.cnae == cnae and lead.municipio == municipio]
            execucao.qtd_leads = len(leads)
            log.info("%d leads do banco neste CNAE e município (coleta e enriquecimento pulados)", len(leads))
        else:
            leads = coletar(cnae=cnae, municipio=municipio)
            execucao.qtd_leads = len(leads)
            log.info("Coletados %d leads", len(leads))

            execucao.qtd_erros += definir_sites_candidatos(leads)

            if rapido:
                log.warning("Modo rápido: sites NÃO verificados e sinais NÃO lidos")
            else:
                log.info("Verificando os sites (pode demorar)")
                execucao.qtd_erros += verificar_sites(leads, nicho, usar_ia=usar_ia)["erro"]
                log.info("Lendo os sinais dos sites confirmados")
                execucao.qtd_erros += enriquecer_sinais(leads)["erro"]

        pontuar_leads(leads)

        if banco is None:
            pass
        elif rapido:
            # no modo rápido o site e os sinais estão incompletos: salvar apagaria o que já foi verificado
            log.warning("Modo rápido: leads NÃO salvos no banco")
        else:
            execucao.qtd_erros += guardar_leads(leads, banco)

        top = selecionar_top(leads, n=qtd_fichas)
        exportar_fichas(top, saida, cidade=cidade)
        com_sinais = sum(1 for lead in top if lead.sinais)
        log.info("%d fichas em %s (%d com sinais registrados)", len(top), saida, com_sinais)
    finally:
        execucao.data_fim = datetime.now()
        duracao = str(execucao.data_fim - execucao.data_inicio).split(".")[0]
        log.info("Execução %s terminou em %s: %d leads, %d erros",
                 execucao.id[:8], duracao, execucao.qtd_leads, execucao.qtd_erros)
        if banco is not None:
            try:
                salvar_execucao(execucao, banco)
            except Exception:
                log.exception("Falha ao salvar a execução no banco")

    if notificador is not None:
        try:
            notificador(montar_resumo(execucao, leads))
        except Exception:
            log.exception("Falha ao enviar o resumo no Telegram")

    return execucao


if __name__ == "__main__":
    def lead_teste(email):
        return Lead(cnpj="11111111000101", razao_social="ESCOLA TESTE LTDA", cnae="8593700",
                    municipio="7107", uf="SP", porte="03", matriz_filial="1",
                    data_abertura=date(2010, 1, 1), email=email)

    # um e-mail inválido (sem @) não derruba o resto
    leads = [lead_teste("contato@escola.com.br"), lead_teste("semarroba"), lead_teste(None)]
    assert definir_sites_candidatos(leads) == 1
    assert leads[0].site == "https://escola.com.br"
    assert leads[1].site is None and leads[2].site is None
    print("Tudo certo")
