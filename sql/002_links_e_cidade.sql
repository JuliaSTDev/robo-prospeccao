
alter table leads add column if not exists links jsonb not null default '{}';

alter table leads add column if not exists cidade text not null default '';