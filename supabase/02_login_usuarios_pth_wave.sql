-- ============================================================
-- HORIZON OEE — PTH/WAVE
-- ETAPA 2: VINCULAR LOGIN NA TABELA EXISTENTE public.usuarios
-- ============================================================
-- IMPORTANTE:
-- NÃO altera a tabela original public.downtime.
-- NÃO remove dados.
-- NÃO altera dados da tabela public.usuarios.
--
-- Este script:
-- 1) adiciona campos de auditoria SOMENTE na tabela nova public.downtime_pth_wave;
-- 2) cria uma função segura para login usando public.usuarios;
-- 3) libera execução da função para anon/authenticated.
-- ============================================================

alter table public.downtime_pth_wave
  add column if not exists criado_por_id integer,
  add column if not exists criado_por_nome text,
  add column if not exists criado_por_email text,
  add column if not exists atualizado_por_id integer,
  add column if not exists atualizado_por_nome text,
  add column if not exists atualizado_por_email text,
  add column if not exists finalizado_por_id integer,
  add column if not exists finalizado_por_nome text,
  add column if not exists finalizado_por_email text;

create index if not exists idx_downtime_pth_wave_criado_por_email
  on public.downtime_pth_wave (criado_por_email);

create index if not exists idx_downtime_pth_wave_finalizado_por_email
  on public.downtime_pth_wave (finalizado_por_email);

-- ============================================================
-- FUNÇÃO DE LOGIN PTH/WAVE
-- ============================================================
-- Usa a tabela existente public.usuarios.
-- Campos esperados pelo print:
-- id, email, senha, nome, setor, role
--
-- Se existir coluna "ativo", ela será respeitada.
-- Aceita ativo como boolean ou texto:
-- true, 1, sim, ativo, active
-- ============================================================

create or replace function public.autenticar_usuario_pth_wave(
  p_email text,
  p_senha text
)
returns table (
  ok boolean,
  mensagem text,
  usuario_id integer,
  nome text,
  email text,
  setor text,
  role text
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_tem_ativo boolean := false;
  v_id integer;
  v_nome text;
  v_email text;
  v_setor text;
  v_role text;
  v_sql text;
begin
  if nullif(trim(coalesce(p_email, '')), '') is null
     or nullif(trim(coalesce(p_senha, '')), '') is null then
    return query
    select
      false,
      'Informe e-mail e senha.'::text,
      null::integer,
      null::text,
      null::text,
      null::text,
      null::text;
    return;
  end if;

  select exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'usuarios'
      and column_name = 'ativo'
  )
  into v_tem_ativo;

  v_sql := '
    select
      u.id::integer,
      u.nome::text,
      u.email::text,
      u.setor::text,
      u.role::text
    from public.usuarios u
    where lower(trim(u.email)) = lower(trim($1))
      and u.senha = $2
  ';

  if v_tem_ativo then
    v_sql := v_sql || '
      and (
        u.ativo is null
        or lower(u.ativo::text) in (''true'', ''1'', ''sim'', ''ativo'', ''active'')
      )
    ';
  end if;

  v_sql := v_sql || ' limit 1';

  execute v_sql
  into v_id, v_nome, v_email, v_setor, v_role
  using p_email, p_senha;

  if v_id is null then
    return query
    select
      false,
      'E-mail/senha inválidos ou usuário desativado.'::text,
      null::integer,
      null::text,
      null::text,
      null::text,
      null::text;
    return;
  end if;

  return query
  select
    true,
    'Login autorizado.'::text,
    v_id,
    v_nome,
    v_email,
    v_setor,
    v_role;
end;
$$;

grant execute on function public.autenticar_usuario_pth_wave(text, text)
to anon, authenticated;

-- Teste opcional:
-- select * from public.autenticar_usuario_pth_wave('email@teste.com', 'senha_teste');
