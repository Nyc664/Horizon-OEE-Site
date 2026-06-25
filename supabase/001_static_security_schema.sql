-- HORIZON OEE STATIC SECURITY — GitHub Pages + Supabase
-- Rode este SQL no Supabase SQL Editor.
-- Ajuste o nome da tabela downtime_pth_wave se seu projeto usar outro nome.

-- 1) Usuários com senha em hash PBKDF2 no navegador
create table if not exists public.horizon_users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  email text,
  display_name text not null,
  role text not null check (role in ('OPERADOR','ADMIN','ADMIN_MASTER')),
  ativo boolean not null default true,

  senha_hash text not null,
  senha_salt text not null,
  senha_algoritmo text not null default 'PBKDF2-SHA256',
  senha_iteracoes integer not null default 150000,

  failed_login_count integer not null default 0,
  locked_until timestamptz,
  last_login_at timestamptz,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 2) Auditoria de ações e tentativas sem permissão
create table if not exists public.horizon_security_events (
  id uuid primary key default gen_random_uuid(),
  action text not null,
  status text not null default 'info',
  user_id uuid,
  user_name text,
  user_role text,
  details jsonb,
  created_at timestamptz not null default now()
);

-- 3) Histórico antes/depois
create table if not exists public.horizon_record_history (
  id uuid primary key default gen_random_uuid(),
  record_id uuid,
  action text not null,
  before_value jsonb,
  after_value jsonb,
  reason text,
  changed_by uuid,
  changed_by_name text,
  created_at timestamptz not null default now()
);

-- 4) Colunas de soft delete e rastreabilidade na tabela atual
alter table public.downtime_pth_wave add column if not exists is_deleted boolean not null default false;
alter table public.downtime_pth_wave add column if not exists deleted_at timestamptz;
alter table public.downtime_pth_wave add column if not exists deleted_by uuid;
alter table public.downtime_pth_wave add column if not exists deleted_by_name text;
alter table public.downtime_pth_wave add column if not exists deleted_reason text;
alter table public.downtime_pth_wave add column if not exists restored_at timestamptz;
alter table public.downtime_pth_wave add column if not exists restored_by uuid;
alter table public.downtime_pth_wave add column if not exists restored_by_name text;
alter table public.downtime_pth_wave add column if not exists restored_reason text;
alter table public.downtime_pth_wave add column if not exists updated_at timestamptz;
alter table public.downtime_pth_wave add column if not exists updated_by uuid;
alter table public.downtime_pth_wave add column if not exists updated_by_name text;
alter table public.downtime_pth_wave add column if not exists created_by uuid;
alter table public.downtime_pth_wave add column if not exists created_by_name text;
alter table public.downtime_pth_wave add column if not exists finalized_at timestamptz;
alter table public.downtime_pth_wave add column if not exists finalized_by uuid;
alter table public.downtime_pth_wave add column if not exists finalized_by_name text;

create index if not exists idx_downtime_pth_wave_deleted on public.downtime_pth_wave(is_deleted);
create index if not exists idx_horizon_events_created_at on public.horizon_security_events(created_at desc);
create index if not exists idx_horizon_history_created_at on public.horizon_record_history(created_at desc);

-- IMPORTANTE:
-- Sem backend e sem Supabase Auth, RLS real por usuário não consegue saber quem é o usuário customizado.
-- Esta versão é uma camada prática para GitHub Pages.
-- Para segurança industrial real, usar backend ou Supabase Auth + RLS.
