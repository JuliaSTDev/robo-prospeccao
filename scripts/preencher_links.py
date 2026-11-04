from robo.armazenamento import carregar_leads, conectar, salvar_leads

banco = conectar()

leads = carregar_leads(banco)

quantos = salvar_leads(leads, banco)

print(f"{quantos} leads atualizados com cidade e links.")