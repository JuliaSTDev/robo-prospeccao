import pytest

from robo.pontuacao import NOTA_MAXIMA, NOTA_MINIMA, pontuar, pontuar_leads

TODOS_POSITIVOS = {"meta_pixel", "google_tag", "whatsapp_no_site", "sem_chat", "filiais"}


@pytest.mark.parametrize("sinais, nota, motivo", [
    ({"meta_pixel", "sem_chat", "filiais"}, 7, "tem pixel, sem chat, tem filiais"),
    ({"sem_site"}, 0, "sem site"),
    (set(), 0, "sem sinais"),
    (TODOS_POSITIVOS, 10,
     "tem pixel, tem Google Tag, WhatsApp no site, sem chat, tem filiais"),
    (TODOS_POSITIVOS | {"sem_site"}, 7,
     "tem pixel, tem Google Tag, WhatsApp no site, sem chat, tem filiais, sem site"),
    ({"site_inacessivel"}, 0, "site fora do ar"),   # -2 nunca deixa a nota abaixo de 0
])
def test_pontuar(sinais, nota, motivo):
    assert pontuar(sinais) == (nota, motivo)


def test_nota_fica_sempre_entre_0_e_10():
    for sinais in (set(), {"sem_site", "site_inacessivel"}, TODOS_POSITIVOS):
        nota, _ = pontuar(sinais)
        assert NOTA_MINIMA <= nota <= NOTA_MAXIMA


def test_sinal_desconhecido_e_ignorado():
    # 'instagram_no_site' e 'so_formulario' ficam registrados, mas ainda não valem pontos
    assert pontuar({"instagram_no_site", "so_formulario"}) == (0, "sem sinais")


def test_lead_sem_site_e_rede_com_filiais(criar_lead):
    sozinha = criar_lead(cnpj="11111111000101", site=None)
    rede_a = criar_lead(cnpj="22222222000101", site="https://a.com.br")
    rede_b = criar_lead(cnpj="22222222000202", site="https://a.com.br")

    pontuar_leads([sozinha, rede_a, rede_b])

    assert (sozinha.nota, sozinha.motivo_da_nota) == (0, "sem site")
    assert (rede_a.nota, rede_a.motivo_da_nota) == (2, "tem filiais")
    assert rede_b.nota == 2


def test_sinais_lidos_do_site_entram_na_nota(criar_lead):
    lead = criar_lead(site="https://escola.com.br", sinais={"meta_pixel", "sem_chat"})

    pontuar_leads([lead])

    assert (lead.nota, lead.motivo_da_nota) == (5, "tem pixel, sem chat")


def test_site_fora_do_ar_aparece_no_motivo(criar_lead):
    # a verificação tira o site (None) e marca 'site_inacessivel'
    lead = criar_lead(site=None, sinais={"site_inacessivel"})

    pontuar_leads([lead])

    assert lead.nota == 0
    assert lead.motivo_da_nota == "sem site, site fora do ar"
