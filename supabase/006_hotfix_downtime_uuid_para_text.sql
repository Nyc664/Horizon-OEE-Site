-- HORIZON OEE — HOTFIX 006
-- Corrige erro ao excluir:
-- invalid input syntax for type uuid: "3"
--
-- Causa provável:
-- algumas colunas de rastreabilidade em downtime_pth_wave foram criadas como uuid
-- em uma versão anterior, mas o sistema usa public.usuarios.id como número inteiro.
--
-- Solução segura:
-- converter as colunas *_by para text. Assim aceita ID numérico do site/EXE
-- e também aceita UUID caso algum registro antigo tenha UUID.
--
-- Não apaga dados.
-- Não altera public.usuarios.senha.
-- Não interfere no login do EXE.

-- 1) Histórico: record_id precisa aceitar id numérico da tabela downtime_pth_wave
alter table public.horizon_record_history
  alter column record_id type text
  using record_id::text;

-- 2) Histórico: changed_by também pode vir de usuarios.id numérico
alter table public.horizon_record_history
  alter column changed_by type text
  using changed_by::text;

-- 3) Auditoria: user_id também pode vir de usuarios.id numérico
alter table public.horizon_security_events
  alter column user_id type text
  using user_id::text;

-- 4) Downtime: colunas de quem criou/editou/excluiu/finalizou/restaurou
alter table public.downtime_pth_wave
  alter column created_by type text
  using created_by::text;

alter table public.downtime_pth_wave
  alter column updated_by type text
  using updated_by::text;

alter table public.downtime_pth_wave
  alter column deleted_by type text
  using deleted_by::text;

alter table public.downtime_pth_wave
  alter column restored_by type text
  using restored_by::text;

alter table public.downtime_pth_wave
  alter column finalized_by type text
  using finalized_by::text;

-- 5) Colunas antigas do login PTH/WAVE, se existirem
alter table public.downtime_pth_wave
  alter column criado_por_id type text
  using criado_por_id::text;

alter table public.downtime_pth_wave
  alter column atualizado_por_id type text
  using atualizado_por_id::text;

alter table public.downtime_pth_wave
  alter column finalizado_por_id type text
  using finalizado_por_id::text;

-- 6) Índices úteis
create index if not exists idx_horizon_record_history_record_id
  on public.horizon_record_history(record_id);

create index if not exists idx_downtime_pth_wave_is_deleted
  on public.downtime_pth_wave(is_deleted);

-- 7) Permissões para GitHub Pages
grant select, insert on table public.horizon_record_history to anon, authenticated;
grant select, insert on table public.horizon_security_events to anon, authenticated;
grant select, insert, update on table public.downtime_pth_wave to anon, authenticated;
