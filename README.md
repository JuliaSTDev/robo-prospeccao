# robo-prospeccao

![Testes](https://github.com/JuliaSTDev/robo-prospeccao/actions/workflows/testes.yml/badge.svg)

Pipeline de prospecção em Python com coletores e enriquecedores plugáveis, nota explicável por sinais e aprovação humana. Inspirado nos actors da Apify.

Gera uma lista de empresas de um nicho e uma cidade, descobre o site de cada uma e exporta uma ficha com links para verificar à mão. Nenhuma abordagem é automática: uma pessoa revisa e aprova antes de qualquer contato.

## Como funciona

1. **Lista:** coleta as empresas ativas do nicho e da cidade na base aberta de CNPJ da Receita.
2. **Site:** descobre o site provável pelo domínio do e-mail cadastral, descartando e-mails gratuitos, contadores e redes.
3. **Ficha:** exporta os melhores leads em Markdown, com links de busca (Google, Instagram, Reclame Aqui, Meta Ad Library). O robô só monta os links, não acessa essas páginas.

## Como rodar

Exemplo para Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

1. Baixe os arquivos da Receita (seção abaixo) e coloque em `data/`, sem descompactar.
2. Rode:
```
   python -X utf8 main.py
```
3. A ficha sai em `data/fichas_top20.md`.

Nicho (CNAE) e cidade (código do município) são definidos no `main.py`.

## Testes

```
pip install -r requirements.txt
pip install -e .
pytest
```

Os testes não usam internet nem chaves: o banco, o Telegram e os sites são trocados por falsos. O GitHub Actions roda o `pytest` a cada push (`.github/workflows/testes.yml`) e o selo no topo mostra o resultado.

## Rodar com Docker

```
docker build -t robo-prospeccao .
docker run --rm robo-prospeccao pytest
docker run --rm --env-file .env -v "${PWD}/data:/app/data" robo-prospeccao python main.py --do-banco
```

O `.env` (chaves) e a pasta `data/` não entram na imagem: são entregues só na hora do `docker run`.

## API

Uma API (FastAPI) lê os leads do Supabase e muda o status deles. É a base do painel.

```
pip install -r requirements.txt
uvicorn robo.api.app:app --reload
```

Abra http://127.0.0.1:8000/docs para ver e testar os endereços:

| Método | Endereço | O que faz |
|---|---|---|
| GET | `/saude` | confirma que a API está no ar |
| GET | `/leads?status=novo&limite=50` | leads de maior nota primeiro (`status` e `limite` são opcionais; `limite` vai de 1 a 200) |
| PATCH | `/leads/{cnpj}/status` | muda o status (`novo`, `aprovado`, `descartado`, `abordado`); corpo: `{"status": "aprovado"}` |

Erros: `404` se o CNPJ não existe, `422` se o dado enviado é inválido, `502` se o Supabase está fora do ar.

**A API não tem senha.** Por isso ela roda só no próprio computador (`127.0.0.1`). Não a exponha na internet antes de ter autenticação.

## Painel

Painel web (Next.js + TypeScript) que mostra a fila de leads: ordenada por nota, com filtros por status, cidade e sinais e uma busca por nome. Ele lê a API do robô no servidor, então a API precisa estar rodando.

Em dois terminais:

```
# terminal 1, na raiz do projeto (ambiente Python ativado)
uvicorn robo.api.app:app --reload

# terminal 2
cd painel
npm install     # só na primeira vez
npm run dev
```

Abra http://localhost:3000. Se a API estiver em outro endereço, defina `API_URL` (por exemplo em `painel/.env.local`, que fica fora do Git).

O painel mostra os 200 leads de maior nota (o limite da API) e filtra por cima deles. Ainda não tem login: roda só no próprio computador.

## Estrutura

```
main.py                         # roda o fluxo: lista -> site -> ficha
src/robo/
  models.py                     # Lead, Sinal, Execucao
  coletores/cnpj_receita.py     # lê a base da Receita e devolve Leads
  enriquecedores/site_do_email.py  # descobre o site pelo e-mail
  exportadores/ficha.py         # seleciona o top e gera a ficha em Markdown
  api/schemas.py                # formato dos dados da API (Pydantic)
  api/app.py                    # os endereços da API (FastAPI)
painel/                         # painel web (Next.js + TypeScript)
scripts/                        # exploração e análise avulsas
data/                           # bases e saídas, fora do Git
```

## Dados: base aberta de CNPJ da Receita Federal

**Fonte:** repositório de arquivos da Receita Federal (SERPRO+), pasta `Dados > Cadastros > CNPJ`.
- Endereço: https://arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK?dir=/Dados/Cadastros/CNPJ
- Mês usado: 2026-10
- A Receita já mudou o endereço mais de uma vez. Se o link quebrar, procure a pasta `Dados > Cadastros > CNPJ` na raiz do repositório.

**Arquivos usados** (salvos em `data/`, fora do Git):

| Arquivo | Conteúdo |
|---|---|
| `Estabelecimentos0.zip` a `9.zip` | Dados de cada estabelecimento (endereço, CNAE, contato, situação) |
| `Empresas0.zip` a `9.zip` | Dados da empresa (razão social, porte, natureza jurídica) |
| `Municipios.zip` | Código do município → nome |
| `Cnaes.zip` | Código CNAE → descrição |

**Formato:** CSV sem cabeçalho, separado por `;`, encoding `latin-1`. Ler sempre com `dtype=str` para não perder zeros à esquerda (CNPJ, CEP).

### Layout de Estabelecimentos (30 colunas)

| Col. | Campo | Observação |
|---|---|---|
| 0 | CNPJ básico | 8 dígitos; liga com o arquivo Empresas |
| 1 | CNPJ ordem | 4 dígitos (`0001` = sede) |
| 2 | CNPJ DV | 2 dígitos. CNPJ completo = col. 0 + 1 + 2 |
| 3 | Matriz/filial | `1` = matriz, `2` = filial |
| 4 | Nome fantasia | Frequentemente vazio |
| 5 | Situação cadastral | `02` = ativa |
| 10 | Data de início da atividade | Formato `AAAAMMDD` |
| 11 | CNAE principal | Ex.: `8593700` = Ensino de idiomas |
| 12 | CNAEs secundários | Vários, separados por vírgula |
| 13 a 17 | Endereço | Tipo, logradouro, número, complemento, bairro |
| 18 | CEP | 8 dígitos |
| 19 | UF | |
| 20 | Município | **Código da Receita**, não do IBGE |
| 21 e 22 | DDD e telefone 1 | Separados |
| 27 | E-mail | Muitas vezes pessoal (Gmail), sobretudo em MEI |

Demais colunas: 6 (data da situação), 7 (motivo), 8 e 9 (exterior), 23 a 26 (telefone 2 e fax), 28 e 29 (situação especial).

### Códigos usados no projeto

| Item | Código |
|---|---|
| CNAE Ensino de idiomas | `8593700` |
| Município São Paulo | `7107` |
| Município Suzano | `7151` |

### Cuidados

- Filtrar município pelo **código**, nunca pelo nome (há cidades homônimas).
- Razão social e porte ficam no arquivo **Empresas**, ligado pelo CNPJ básico.
- A base tem placeholders (telefones como `0000000000`, e-mails inválidos). O coletor valida na entrada.
- O e-mail cadastral pode ser do contador ou de outra empresa. O site descoberto por ele é só um palpite, por isso a ficha o marca como "não verificado".
- **LGPD:** a base contém dados de contato de pessoas físicas (MEI). Empresário individual e MEI são excluídos. Os dados ficam fora do Git, não se publicam CNPJ, e-mail ou telefone reais, e o uso é só para contato comercial B2B pertinente.

Para explorar a base: `python scripts/explorar_cnpj.py`

## Status

- Pronto: coletor da Receita, descoberta de site pelo e-mail, ficha com links de verificação.
- Próximos passos: limpeza de dados, leitura do site com sinais (WhatsApp, pixel, chat), nota de 0 a 100 com motivo, banco SQLite e resumo no Telegram.