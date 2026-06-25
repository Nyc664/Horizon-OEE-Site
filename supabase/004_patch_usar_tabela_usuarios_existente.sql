-- HORIZON OEE — PATCH PARA USAR A TABELA EXISTENTE public.usuarios
-- Rode no Supabase SQL Editor.
-- NÃO cria horizon_users.

create table if not exists public.horizon_security_events (
  id uuid primary key default gen_random_uuid(),
  action text not null,
  status text not null default 'info',
  user_id integer,
  user_name text,
  user_role text,
  details jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.horizon_record_history (
  id uuid primary key default gen_random_uuid(),
  record_id uuid,
  action text not null,
  before_value jsonb,
  after_value jsonb,
  reason text,
  changed_by integer,
  changed_by_name text,
  created_at timestamptz not null default now()
);

alter table public.usuarios add column if not exists senha_hash text;
alter table public.usuarios add column if not exists senha_salt text;
alter table public.usuarios add column if not exists senha_algoritmo text default 'PBKDF2-SHA256';
alter table public.usuarios add column if not exists senha_iteracoes integer default 150000;
alter table public.usuarios add column if not exists failed_login_count integer not null default 0;
alter table public.usuarios add column if not exists locked_until timestamptz;
alter table public.usuarios add column if not exists last_login_at timestamptz;
alter table public.usuarios add column if not exists updated_at timestamptz default now();

alter table public.downtime_pth_wave add column if not exists is_deleted boolean not null default false;
alter table public.downtime_pth_wave add column if not exists deleted_at timestamptz;
alter table public.downtime_pth_wave add column if not exists deleted_by integer;
alter table public.downtime_pth_wave add column if not exists deleted_by_name text;
alter table public.downtime_pth_wave add column if not exists deleted_reason text;
alter table public.downtime_pth_wave add column if not exists restored_at timestamptz;
alter table public.downtime_pth_wave add column if not exists restored_by integer;
alter table public.downtime_pth_wave add column if not exists restored_by_name text;
alter table public.downtime_pth_wave add column if not exists restored_reason text;
alter table public.downtime_pth_wave add column if not exists updated_at timestamptz;
alter table public.downtime_pth_wave add column if not exists updated_by integer;
alter table public.downtime_pth_wave add column if not exists updated_by_name text;
alter table public.downtime_pth_wave add column if not exists created_by integer;
alter table public.downtime_pth_wave add column if not exists created_by_name text;
alter table public.downtime_pth_wave add column if not exists finalized_at timestamptz;
alter table public.downtime_pth_wave add column if not exists finalized_by integer;
alter table public.downtime_pth_wave add column if not exists finalized_by_name text;

create index if not exists idx_downtime_pth_wave_deleted on public.downtime_pth_wave(is_deleted);
create index if not exists idx_horizon_events_created_at on public.horizon_security_events(created_at desc);
create index if not exists idx_horizon_history_created_at on public.horizon_record_history(created_at desc);

grant usage on schema public to anon, authenticated;
grant select, update on table public.usuarios to anon, authenticated;
grant select, insert on table public.horizon_security_events to anon, authenticated;
grant select, insert on table public.horizon_record_history to anon, authenticated;
grant select, insert, update on table public.downtime_pth_wave to anon, authenticated;
