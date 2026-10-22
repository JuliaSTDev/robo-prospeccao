"""Usa a IA gratuita (Groq) para decidir os casos duvidosos."""
import json
import os

from dotenv import load_dotenv
from groq import Groq

from robo.enriquecedores.site_confere import _texto_visivel

load_dotenv()

cliente = Groq(api_key=os.environ["GROQ_API_KEY"])
MODELO = os.environ.get("GROQ_MODELO", "openai/gpt-oss-20b")

DESCRICAO_NICHO = {
    "educacao": "escola de idiomas, curso livre ou escola particular",
    "estetica": "clínica de estética",
}

PROMPT = """Você verifica se um site pertence a uma empresa específica.

Empresa: {nome}
Tipo esperado: {tipo}
Endereço do site: {url}

Texto do site (resumo):
\"\"\"{texto}\"\"\"

Responda SÓ com JSON neste formato:
{{"confere": true ou false, "confianca": "alta" | "media" | "baixa", "motivo": "frase curta"}}

"confere" é true apenas se o site for da própria empresa E ela for do tipo esperado.
Portal de notícias, marketplace, diretório, rede social ou site de outra empresa = false."""


def confere_com_ia(html: str, nome: str, nicho: str, url: str) -> tuple[bool, str]:
    texto = _texto_visivel(html)[:3000]
    try:
        resposta = cliente.chat.completions.create(
            model=MODELO,
            temperature=0,
            reasoning_effort="low",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": PROMPT.format(
                nome=nome, tipo=DESCRICAO_NICHO[nicho], url=url, texto=texto)}],
        )
    except Exception as e:  # modelo inexistente, limite da cota, rede...
        return False, f"IA indisponível ({type(e).__name__}), revisar"

    try:
        dados = json.loads(resposta.choices[0].message.content)
        return bool(dados.get("confere")), f"IA ({dados.get('confianca')}): {dados.get('motivo')}"
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return False, "IA: resposta inválida, revisar"