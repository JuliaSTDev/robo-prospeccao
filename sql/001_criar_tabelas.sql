-- Tabelas do robô de prospecção. Cole no Supabase: SQL Editor > New query > Run.
-- Pode rodar mais de uma vez: "if not exists" evita erro e não apaga nada.

create table if not exists leads (
    cnpj            text primary key,              -- CNPJ completo (14 dígitos): um lead por estabelecimento
    razao_social    text not null,
    nome_fantasia   text,
    cnae            text not null,
    municipio       text not null,
    uf              text not null,
    porte           text not null,
    matriz_filial   text not null,
    data_abertura   date,
    telefone        text,
    email           text,
    site            text,
    site_situacao   text,                          -- confere, sem_site, nao_confere, inacessivel, bloqueado, revisar
    site_motivo     text not null default '',
    sinais          text[] not null default '{}',  -- ex.: {meta_pixel,sem_chat}
    nota            integer not null default 0,    -- 0 a 10
    motivo_da_nota  text not null default '',
    status          text not null default 'novo',  -- só a Julia muda (o robô nunca sobrescreve)
    coletado_em     timestamp not null default now(),
    criado_em       timestamptz not null default now()
);

create index if not exists leads_status_nota_idx on leads (status, nota desc);

create table if not exists execucoes (
    id           text primary key,
    data_inicio  timestamp not null,
    data_fim     timestamp,
    parametros   jsonb not null default '{}',
    qtd_leads    integer not null default 0,
    qtd_erros    integer not null default 0
);

-- Segurança: com o RLS ligado e nenhuma política criada, a chave pública (anon) não lê nada.
-- Só a chave secreta do robô (que ignora o RLS) consegue ler e gravar.
alter table leads     enable row level security;
alter table execucoes enable row level security;
