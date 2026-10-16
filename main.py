from datetime import date

from robo.models import Execucao, Lead, Sinal

execucao = Execucao(parametros={"nicho": "8593700", "cidade": "SAO PAULO"})

lead = Lead(
    cnpj="00623904000173",
    razao_social="ESCOLA DE IDIOMAS EXEMPLO LTDA",
    cnae="8593700",
    municipio="SAO PAULO",
    uf="SP",
    porte="ME",
    data_abertura=date(2015, 3, 12),
    matriz_filial="matriz",
)

sinal = Sinal(lead_cnpj=lead.cnpj, fonte="site", tipo="whatsapp", valor="wa.me/5511999999999")

print(execucao)
print(lead)
print(sinal)