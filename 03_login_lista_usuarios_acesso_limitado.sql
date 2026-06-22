-- ============================================================
-- HORIZON OEE — PTH/WAVE
-- LOGIN POR LISTA + ACESSO LIMITADO PARA OPERADOR
-- ============================================================
-- NÃO altera a tabela original public.downtime.
-- NÃO apaga dados.
-- NÃO altera dados da tabela public.usuarios.
--
-- Operador:
-- - aparece na lista;
-- - NÃO precisa de senha;
-- - pode abrir chamado/parada;
-- - NÃO pode finalizar;
-- - NÃO pode apagar;
-- - NÃO pode editar registro salvo.
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

create or replace function public.listar_usuarios_pth_wave()
returns table (
  usuario_id integer,
  nome text,
  email text,
  setor text,
  role text,
  perfil_exibicao text,
  requer_senha boolean,
  nivel_acesso text,
  pode_abrir boolean,
  pode_finalizar boolean,
  pode_apagar boolean,
  pode_editar boolean
)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_tem_ativo boolean := false;
  v_sql text;
begin
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name = 'usuarios'
      and column_name = 'ativo'
  ) into v_tem_ativo;

  v_sql := '
    select
      u.id::integer,
      coalesce(nullif(trim(u.nome), ''''), u.email)::text,
      u.email::text,
      u.setor::text,
      u.role::text,
      coalesce(nullif(trim(u.role), ''''), nullif(trim(u.setor), ''''), ''Usuário'')::text,
      case when lower(coalesce(u.role, '''') || '' '' || coalesce(u.setor, '''') || '' '' || coalesce(u.nome, '''')) like ''%operador%'' then false else true end,
      case when lower(coalesce(u.role, '''') || '' '' || coalesce(u.setor, '''') || '' '' || coalesce(u.nome, '''')) like ''%operador%'' then ''operador'' else ''admin'' end,
      true,
      case when lower(coalesce(u.role, '''') || '' '' || coalesce(u.setor, '''') || '' '' || coalesce(u.nome, '''')) like ''%operador%'' then false else true end,
      case when lower(coalesce(u.role, '''') || '' '' || coalesce(u.setor, '''') || '' '' || coalesce(u.nome, '''')) like ''%operador%'' then false else true end,
      case when lower(coalesce(u.role, '''') || '' '' || coalesce(u.setor, '''') || '' '' || coalesce(u.nome, '''')) like ''%operador%'' then false else true end
    from public.usuarios u
    where u.email is not null
  ';

  if v_tem_ativo then
    v_sql := v_sql || '
      and (
        u.ativo is null
        or lower(u.ativo::text) in (''true'', ''1'', ''sim'', ''ativo'', ''active'')
      )
    ';
  end if;

  v_sql := v_sql || ' order by lower(coalesce(nullif(trim(u.nome), ''''), u.email)) ';
  return query execute v_sql;
end;
$$;

grant execute on function public.listar_usuarios_pth_wave()
to anon, authenticated;

create or replace function public.autenticar_usuario_pth_wave_lista(
  p_usuario_id integer,
  p_senha text default null
)
returns table (
  ok boolean,
  mensagem text,
  usuario_id integer,
  nome text,
  email text,
  setor text,
  role text,
  perfil_exibicao text,
  requer_senha boolean,
  nivel_acesso text,
  pode_abrir boolean,
  pode_finalizar boolean,
  pode_apagar boolean,
  pode_editar boolean
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
  v_senha text;
  v_operador boolean;
  v_sql text;
begin
  if p_usuario_id is null then
    return query select false, 'Selecione um usuário.'::text, null::integer, null::text, null::text, null::text, null::text, null::text, null::boolean, null::text, null::boolean, null::boolean, null::boolean, null::boolean;
    return;
  end if;

  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name = 'usuarios'
      and column_name = 'ativo'
  ) into v_tem_ativo;

  v_sql := '
    select
      u.id::integer,
      coalesce(nullif(trim(u.nome), ''''), u.email)::text,
      u.email::text,
      u.setor::text,
      u.role::text,
      u.senha::text
    from public.usuarios u
    where u.id = $1
  ';

  if v_tem_ativo then
    v_sql := v_sql || '
      and (
        u.ativo is null
        or lower(u.ativo::text) in (''true'', ''1'', ''sim'', ''ativo'', ''active'')
      )
    ';
  end if;

  v_sql := v_sql || ' limit 1 ';

  execute v_sql into v_id, v_nome, v_email, v_setor, v_role, v_senha using p_usuario_id;

  if v_id is null then
    return query select false, 'Usuário não encontrado ou desativado.'::text, null::integer, null::text, null::text, null::text, null::text, null::text, null::boolean, null::text, null::boolean, null::boolean, null::boolean, null::boolean;
    return;
  end if;

  v_operador := lower(coalesce(v_role, '') || ' ' || coalesce(v_setor, '') || ' ' || coalesce(v_nome, '')) like '%operador%';

  if not v_operador then
    if coalesce(p_senha, '') <> coalesce(v_senha, '') then
      return query select false, 'Senha inválida para este usuário.'::text, null::integer, null::text, null::text, null::text, null::text, null::text, null::boolean, null::text, null::boolean, null::boolean, null::boolean, null::boolean;
      return;
    end if;
  end if;

  return query
  select
    true,
    case when v_operador then 'Login autorizado. Operador com acesso limitado.' else 'Login autorizado.' end::text,
    v_id,
    v_nome,
    v_email,
    v_setor,
    v_role,
    coalesce(nullif(trim(v_role), ''), nullif(trim(v_setor), ''), 'Usuário')::text,
    (not v_operador),
    case when v_operador then 'operador' else 'admin' end::text,
    true,
    (not v_operador),
    (not v_operador),
    (not v_operador);
end;
$$;

grant execute on function public.autenticar_usuario_pth_wave_lista(integer, text)
to anon, authenticated;

-- Testes opcionais:
-- select * from public.listar_usuarios_pth_wave();
-- select * from public.autenticar_usuario_pth_wave_lista(1, null);
