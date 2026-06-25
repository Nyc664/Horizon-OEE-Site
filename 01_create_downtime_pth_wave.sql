-- ============================================================
-- HORIZON OEE — PTH/WAVE
-- NOVA TABELA PARA PARADAS PTH/WAVE
-- ============================================================
-- IMPORTANTE:
-- Este script NÃO altera a tabela original "downtime".
-- Ele cria uma tabela separada: public.downtime_pth_wave
--
-- Execute no Supabase:
-- SQL Editor > New query > cole este script > Run
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.downtime_pth_wave (
  id uuid primary key default gen_random_uuid(),

  status text not null default 'EM ABERTURA'
    check (status in ('EM ABERTURA', 'CONCLUÍDO')),

  origem text not null default 'PTH/WAVE',

  data_registro date not null default current_date,

  linha text not null
    check (linha in ('PTH/Wave 1', 'PTH/Wave 2')),

  op text,

  hora_inicio time without time zone not null,
  hora_fim time without time zone,

  motivo text not null
    check (motivo in (
      'Manutenção',
      'Parada por Processo',
      'Setup',
      'Falta de Material',
      'Qualidade'
    )),

  obs text not null default '',
  suporte boolean not null default false,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_downtime_pth_wave_status
  on public.downtime_pth_wave (status);

create index if not exists idx_downtime_pth_wave_data
  on public.downtime_pth_wave (data_registro desc);

create index if not exists idx_downtime_pth_wave_linha
  on public.downtime_pth_wave (linha);

create index if not exists idx_downtime_pth_wave_created_at
  on public.downtime_pth_wave (created_at desc);

create or replace function public.set_downtime_pth_wave_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_downtime_pth_wave_updated_at on public.downtime_pth_wave;

create trigger trg_downtime_pth_wave_updated_at
before update on public.downtime_pth_wave
for each row
execute function public.set_downtime_pth_wave_updated_at();

alter table public.downtime_pth_wave enable row level security;

grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.downtime_pth_wave to anon, authenticated;

drop policy if exists "downtime_pth_wave_select" on public.downtime_pth_wave;
drop policy if exists "downtime_pth_wave_insert" on public.downtime_pth_wave;
drop policy if exists "downtime_pth_wave_update" on public.downtime_pth_wave;
drop policy if exists "downtime_pth_wave_delete" on public.downtime_pth_wave;

-- ============================================================
-- POLICIES PARA PROTÓTIPO VIA GITHUB PAGES
-- ============================================================
-- Como o site ainda não tem login, estas policies permitem leitura,
-- criação, edição e exclusão usando a publishable/anon key.
--
-- Para produção, o ideal é adicionar autenticação e restringir por usuário.
-- ============================================================

create policy "downtime_pth_wave_select"
on public.downtime_pth_wave
for select
to anon, authenticated
using (true);

create policy "downtime_pth_wave_insert"
on public.downtime_pth_wave
for insert
to anon, authenticated
with check (true);

create policy "downtime_pth_wave_update"
on public.downtime_pth_wave
for update
to anon, authenticated
using (true)
with check (true);

create policy "downtime_pth_wave_delete"
on public.downtime_pth_wave
for delete
to anon, authenticated
using (true);

-- Teste opcional depois de executar:
-- select * from public.downtime_pth_wave order by created_at desc;
