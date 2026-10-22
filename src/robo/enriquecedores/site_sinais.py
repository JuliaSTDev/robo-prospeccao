"""Detecta no HTML do site: WhatsApp, chat/bot instalado, sistema de agenda ou matrícula e redes."""
import re
from dataclasses import dataclass, field

# --- WhatsApp -------------------------------------------------------------
PADROES_WHATSAPP = [
    r"wa\.me/(\+?\d{10,15})",
    r"api\.whatsapp\.com/send/?\?[^\"'>]*phone=(\+?\d{10,15})",
    r"web\.whatsapp\.com/send/?\?[^\"'>]*phone=(\+?\d{10,15})",
    r"whatsapp://send/?\?[^\"'>]*phone=(\+?\d{10,15})",
]
# botões flutuantes de WhatsApp (não são atendimento automático)
PLUGINS_BOTAO_WHATSAPP = {
    "joinchat": "Joinchat", "getbutton.io": "GetButton", "click-to-chat": "Click to Chat",
    "elfsight": "Elfsight",
}

# --- Chats e bots já instalados (concorrência ou ponto de integração) -----
CHATS = {
    "embed.tawk.to": "Tawk.to",
    "jivosite": "JivoChat", "jivochat": "JivoChat",
    "zdassets.com": "Zendesk", "zopim": "Zendesk",
    "widget.intercom.io": "Intercom", "intercomcdn": "Intercom",
    "client.crisp.chat": "Crisp",
    "code.tidio.co": "Tidio",
    "js.driftt.com": "Drift",
    "freshchat": "Freshchat",
    "usemessages.com": "HubSpot Chat",
    "octadesk": "Octadesk",
    "blip.ai": "Blip", "take.net": "Blip",
    "manychat": "ManyChat",
    "kommo": "Kommo", "amocrm": "Kommo",
    "zenvia": "Zenvia",
    "chatbase": "Chatbase",
}

# --- Sistemas de agenda / matrícula (o que você vai integrar depois) ------
SISTEMAS = {
    "educacao": {
        "sponte": "Sponte", "sophia.com.br": "Sophia", "gennera": "Gennera",
        "ischolar": "iScholar", "classapp": "ClassApp", "agendaedu": "Agenda Edu",
        "moodle": "Moodle",
    },
    "estetica": {
        "trinks.com": "Trinks", "agendapro": "AgendaPro", "booksy": "Booksy",
        "doctoralia": "Doctoralia", "feegow": "Feegow", "simplesagenda": "Simples Agenda",
    },
    "geral": {"calendly.com": "Calendly", "hotmart": "Hotmart"},
}
TERMOS_ONLINE = {
    "educacao": ["matricula online", "matricule-se", "portal do aluno", "area do aluno"],
    "estetica": ["agendamento online", "agende online", "agende agora", "agendar horario"],
}

REDES = {
    "instagram": r"instagram\.com/([A-Za-z0-9_.]+)",
    "facebook": r"facebook\.com/([A-Za-z0-9_.\-]+)",
}


@dataclass
class SinaisSite:
    tem_whatsapp: bool = False
    whatsapp_numero: str = ""
    botao_whatsapp: str = ""                       # plugin do botão, se houver
    chats: list[str] = field(default_factory=list)  # chats/bots detectados
    sistemas: list[str] = field(default_factory=list)
    tem_agendamento_online: bool = False
    tem_formulario: bool = False
    instagram: str = ""
    facebook: str = ""

    @property
    def tem_chat(self) -> bool:
        return bool(self.chats)

    @property
    def pontos_encaixe(self) -> int:
        """+1 se tem WhatsApp e ainda não tem chat/bot (porta aberta para o agente)."""
        return 1 if self.tem_whatsapp and not self.tem_chat else 0

    def resumo(self) -> str:
        partes = []
        partes.append("WA" if self.tem_whatsapp else "sem WA")
        partes.append("chat: " + ", ".join(self.chats) if self.chats else "sem chat")
        if self.sistemas:
            partes.append("sist: " + ", ".join(self.sistemas))
        elif self.tem_agendamento_online:
            partes.append("agenda/matrícula online")
        return " | ".join(partes)


def _normalizar_numero(numero: str) -> str:
    digitos = re.sub(r"\D", "", numero)
    return digitos if digitos.startswith("55") else f"55{digitos}"


def detectar_sinais(html: str, nicho: str) -> SinaisSite:
    s = SinaisSite()
    bruto = html or ""
    baixo = bruto.lower()

    # WhatsApp
    for padrao in PADROES_WHATSAPP:
        m = re.search(padrao, bruto, flags=re.I)
        if m:
            s.tem_whatsapp = True
            s.whatsapp_numero = _normalizar_numero(m.group(1))
            break
    if not s.tem_whatsapp and "whatsapp" in baixo and ("wa.me" in baixo or "api.whatsapp" in baixo):
        s.tem_whatsapp = True
    for chave, nome in PLUGINS_BOTAO_WHATSAPP.items():
        if chave in baixo:
            s.tem_whatsapp, s.botao_whatsapp = True, nome
            break

    # Chats e bots
    s.chats = sorted({nome for chave, nome in CHATS.items() if chave in baixo})

    # Sistemas
    catalogo = {**SISTEMAS.get(nicho, {}), **SISTEMAS["geral"]}
    s.sistemas = sorted({nome for chave, nome in catalogo.items() if chave in baixo})

    from robo.enriquecedores.site_confere import _texto_visivel  # evita import no topo
    texto = _texto_visivel(bruto)
    s.tem_agendamento_online = bool(s.sistemas) or any(t in texto for t in TERMOS_ONLINE.get(nicho, []))

    # Formulário e redes
    s.tem_formulario = "<form" in baixo
    for rede, padrao in REDES.items():
        m = re.search(padrao, bruto, flags=re.I)
        if m and m.group(1).lower() not in {"sharer", "share", "tr", "plugins", "p"}:
            setattr(s, rede, m.group(1))

    return s