-- Rollback opcional
-- Use somente se quiser remover a tabela PTH/WAVE criada.
-- NÃO afeta a tabela original downtime.

drop table if exists public.downtime_pth_wave cascade;
drop function if exists public.set_downtime_pth_wave_updated_at() cascade;
