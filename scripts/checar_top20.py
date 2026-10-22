import time
from collections import Counter

from robo.coletores.cnpj_receita import coletar
from robo.enriquecedores.site_confere import confere_site
from robo.enriquecedores.site_confere_ia import confere_com_ia
from robo.enriquecedores.site_do_email import site_candidato
from robo.enriquecedores.site_responde import ABRIU, BLOQUEADO, FORA_DO_AR, checar_site
from robo.enriquecedores.site_sinais import detectar_sinais
from robo.exportadores.ficha import selecionar_top
from robo.pontuacao import pontuar_leads

PAUSA_SEGUNDOS = 2
NICHO = "educacao"
DUVIDOSOS = ("nome bate", "nicho bate", "nome genérico")

leads = coletar(cnae="8593700", municipio="7107")
for lead in leads:
    lead.site = site_candidato(lead.email)
pontuar_leads(leads)
top = selecionar_top(leads, n=20)

contagem = Counter()
confere_contagem = Counter()
usou_ia = 0

for lead in top:
    if lead.site is None:
        print(f"{'SEM SITE':<11} {'-':<38} {'-':<55} {lead.razao_social}")
        continue

    # 1. o site abre?
    res = checar_site(lead.site)
    situacao, detalhe = res
    contagem[situacao] += 1

    motivo = detalhe if situacao != ABRIU else "-"
    ok = False

    # 2. o site é mesmo da empresa? (regras primeiro, IA só nos duvidosos)
    if situacao == ABRIU:
        nome = getattr(lead, "nome_fantasia", None) or lead.razao_social

        ok, motivo = confere_site(res.html, nome, NICHO, res.url_final)
        if not ok and motivo.startswith(DUVIDOSOS):
            ok, motivo = confere_com_ia(res.html, nome, NICHO, res.url_final)
            usou_ia += 1

        # IA com confiança baixa: não descarta, manda para revisão manual
        if motivo.startswith("IA (baixa)"):
            confere_contagem["revisar"] += 1
        else:
            confere_contagem["confere" if ok else "nao_confere"] += 1

    # 3. sinais do site (só nos que abriram e conferem)
    sinais_txt = "-"
    if situacao == ABRIU and ok:
        sinais = detectar_sinais(res.html, NICHO)
        sinais_txt = f"{sinais.resumo()} (+{sinais.pontos_encaixe})"
        if sinais.pontos_encaixe:
            confere_contagem["porta_aberta"] += 1

    print(f"{situacao:<11} {motivo[:38]:<38} {sinais_txt[:55]:<55} {lead.site}")
    time.sleep(PAUSA_SEGUNDOS)

print(
    f"\n{contagem[ABRIU]} abriram, "
    f"{contagem[BLOQUEADO]} bloquearam robô, "
    f"{contagem[FORA_DO_AR]} fora do ar"
)
print(
    f"Dos que abriram: {confere_contagem['confere']} conferem, "
    f"{confere_contagem['nao_confere']} não conferem, "
    f"{confere_contagem['revisar']} para revisar "
    f"(IA consultada em {usou_ia})"
)
print(f"Com WhatsApp e sem chat (porta aberta para o agente): {confere_contagem['porta_aberta']}")