# robo-prospeccao
Pipeline de prospecção em Python com coletores e enriquecedores plugáveis, nota explicável por sinais e aprovação humana.

## Dados: base aberta de CNPJ da Receita Federal

**Fonte:** repositório de arquivos da Receita Federal (SERPRO+), pasta `Dados > Cadastros > CNPJ`.
- Endereço: (https://arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK?dir=/Dados/Cadastros/CNPJ)
- Mês usado: 2026-10
- A Receita já mudou o endereço mais de uma vez. Se o link quebrar, procure a pasta `Dados > Cadastros > CNPJ` na raiz do repositório.

**Arquivos usados** (salvos em `data/`, fora do Git):

| Arquivo | Conteúdo |
|---|---|
| `Estabelecimentos0.zip` a `9.zip` | Dados de cada estabelecimento (endereço, CNAE, contato, situação) |
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
- **LGPD:** a base contém dados de contato de pessoas físicas (MEI). Os dados ficam fora do Git e são usados só para contato comercial B2B pertinente.

Para explorar a base: `python scripts/explorar_cnpj.py`
