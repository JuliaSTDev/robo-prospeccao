"""Orquestra o robô: coletar -> enriquecer -> pontuar -> exportar as fichas.

Se uma peça falhar em UM lead, o erro vai para o log e o pipeline segue com os outros.
Cada execução é descrita por uma Execucao (início, fim, quantos leads, quantos erros).
"""
import logging
from datetime import date, datetime

from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_do_email import site_candidato
from robo.enriquecedores.site_sinais import enriquecer_sinais
from robo.enriquecedores.verificar_site import verificar_sites
from robo.exportadores.ficha import exportar_fichas, selecionar_top
from robo.models import Execucao, Lead
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


def rodar(cnae: str, municipio: str, nicho: str, cidade: str, saida: str,
          usar_ia: bool = True, rapido: bool = False, qtd_fichas: int = 20) -> Execucao:
    """Roda o robô de ponta a ponta e devolve o registro da execução."""
    execucao = Execucao(parametros={
        "cnae": cnae, "municipio": municipio, "nicho": nicho,
        "ia": str(usar_ia), "rapido": str(rapido),
    })
    log.info("Execução %s iniciada: %s", execucao.id[:8], execucao.parametros)

    try:
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
        top = selecionar_top(leads, n=qtd_fichas)
        exportar_fichas(top, saida, cidade=cidade)
        com_sinais = sum(1 for lead in top if lead.sinais)
        log.info("%d fichas em %s (%d com sinais registrados)", len(top), saida, com_sinais)
    finally:
        execucao.data_fim = datetime.now()
        duracao = str(execucao.data_fim - execucao.data_inicio).split(".")[0]
        log.info("Execução %s terminou em %s: %d leads, %d erros",
                 execucao.id[:8], duracao, execucao.qtd_leads, execucao.qtd_erros)

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