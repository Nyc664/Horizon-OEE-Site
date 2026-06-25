const CONFIG = window.HORIZON_CONFIG;
let db = null;
let usuario = null;
let usuarios = [];
let registros = [];
let currentView = "registros";
let selectedId = null;
let modoEdicaoId = null;
let inactivityTimer = null;
let tickTimer = null;
let lastActivity = Date.now();

const refs = {};

document.addEventListener("DOMContentLoaded", init);

function $(id){ return document.getElementById(id); }
function esc(v){ return String(v ?? "").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m])); }
function nowISO(){ return new Date().toISOString(); }
function hojeISO(){ return new Date().toISOString().slice(0,10); }
function hojeBR(){ return new Date().toLocaleDateString("pt-BR"); }
function horaAgora(){ return new Date().toTimeString().slice(0,5); }
function dataBR(v){ if(!v) return "—"; const [y,m,d] = String(v).slice(0,10).split("-"); return d&&m&&y ? `${d}/${m}/${y}` : v; }
function horaCurta(v){ return v ? String(v).slice(0,5) : "—"; }
function f(){ return CONFIG.usuarioCampos || {}; }
function userId(u){ return u?.[f().id || "id"]; }
function userNome(u){ return u?.[f().nome || "nome"] || u?.[f().email || "email"] || "Usuário"; }
function userEmail(u){ return u?.[f().email || "email"]; }

function normalizeRole(u){
  const txt = `${u?.role || ""} ${u?.setor || ""} ${u?.nome || ""}`.toLowerCase();
  if(txt.includes("master") || txt.includes("admin_master")) return "ADMIN_MASTER";
  if(txt.includes("admin") || txt.includes("tecnico") || txt.includes("técnico") || txt.includes("processo")) return "ADMIN";
  return "OPERADOR";
}

function mapRefs(){
  [
    "statusBox","tbodyRegistros","tableInfo","kpiAbertos","kpiConcluidos","kpiLixeira","kpiAcesso","kpiPerfil","viewTitle","sessionChip","userLabel","sessionTimer",
    "btnNovo","btnRefresh","btnLogout","btnMenu","sideMenu","shade","btnCloseMenu","menuRegistros","menuLixeira","menuAuditoria","menuHistorico","menuBackup",
    "loginBackdrop","loginForm","loginUsuario","loginSenha","loginAlert","loginResumo","btnSetupAdmin","drawerBackdrop","btnFechar","registroForm","formTitle","formAlert",
    "data","inicio","fim","linha","op","motivo","obs","chars","suporte","statusForm","btnSalvar","btnEncerrar","btnApagar","btnRestaurar","genericModal","modalTitle",
    "modalText","modalContent","modalCancel","modalOk"
  ].forEach(id => refs[id] = $(id));
}

async function init(){
  mapRefs();

  if(!CONFIG.supabaseUrl || CONFIG.supabaseUrl.includes("COLE_AQUI") || CONFIG.supabaseUrl.includes("/rest/v1")){
    setStatus("Corrija web/js/config.js: use só https://xxxx.supabase.co, sem /rest/v1.", "error");
    showLogin();
    return;
  }

  if(!CONFIG.supabaseAnonKey || CONFIG.supabaseAnonKey.includes("COLE_AQUI")){
    setStatus("Configure web/js/config.js com sua publishable/anon key do Supabase.", "error");
    showLogin();
    return;
  }

  if(!window.supabase){
    setStatus("Biblioteca Supabase não carregou.", "error");
    return;
  }

  db = window.supabase.createClient(CONFIG.supabaseUrl, CONFIG.supabaseAnonKey);
  usuario = HorizonSecurity.getSession();

  bindEvents();
  fillSelects();
  setupInactivity();

  await carregarUsuarios();

  if(usuario){
    aplicarUsuario();
    await carregarRegistros();
  } else {
    showLogin();
  }
}

function bindEvents(){
  refs.btnNovo.onclick = novo;
  refs.btnRefresh.onclick = carregarRegistros;
  refs.btnLogout.onclick = () => logout("Logout manual.");
  refs.btnMenu.onclick = openMenu;
  refs.btnCloseMenu.onclick = closeMenu;
  refs.shade.onclick = closeMenu;

  refs.menuRegistros.onclick = () => changeView("registros");
  refs.menuLixeira.onclick = () => changeView("lixeira");
  refs.menuAuditoria.onclick = () => changeView("auditoria");
  refs.menuHistorico.onclick = () => changeView("historico");
  refs.menuBackup.onclick = backupView;

  refs.loginForm.onsubmit = login;
  refs.loginUsuario.onchange = resumoLogin;
  refs.btnSetupAdmin.classList.add("hide");

  refs.btnFechar.onclick = fecharDrawer;
  refs.drawerBackdrop.onclick = e => { if(e.target === refs.drawerBackdrop) fecharDrawer(); };
  refs.registroForm.onsubmit = salvarRegistro;
  refs.btnEncerrar.onclick = encerrarRegistro;
  refs.btnApagar.onclick = apagarRegistro;
  refs.btnRestaurar.onclick = restaurarRegistro;
  refs.obs.oninput = () => refs.chars.textContent = `${refs.obs.value.length} caracteres`;
}

function setupInactivity(){
  ["mousemove","mousedown","keydown","touchstart","scroll"].forEach(ev => window.addEventListener(ev, () => {
    lastActivity = Date.now();
    resetInactivityTimer();
  }, {passive:true}));

  resetInactivityTimer();

  tickTimer = setInterval(() => {
    if(!usuario){
      refs.sessionTimer.textContent = "sem sessão";
      return;
    }
    const left = Math.max(0, CONFIG.sessaoInatividadeMs - (Date.now() - lastActivity));
    refs.sessionTimer.textContent = `cai em ${Math.ceil(left/1000)}s`;
  }, 1000);
}

function resetInactivityTimer(){
  clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
    if(usuario) logout("Sessão expirada por 5 minutos de inatividade.");
  }, CONFIG.sessaoInatividadeMs);
}

function setStatus(msg, type=""){
  refs.statusBox.textContent = msg;
  refs.statusBox.className = `notice ${type}`;
}

function showLogin(){
  refs.loginBackdrop.classList.add("show");
  refs.loginSenha.value = "";
}

function hideLogin(){
  refs.loginBackdrop.classList.remove("show");
}

function alertLogin(msg){
  refs.loginAlert.textContent = msg;
  refs.loginAlert.classList.add("show");
}

function clearLoginAlert(){
  refs.loginAlert.classList.remove("show");
  refs.loginAlert.textContent = "";
}

function alertForm(msgs){
  refs.formAlert.innerHTML = Array.isArray(msgs) ? msgs.map(esc).join("<br>") : esc(msgs);
  refs.formAlert.classList.add("show");
}

function clearFormAlert(){
  refs.formAlert.classList.remove("show");
  refs.formAlert.textContent = "";
}

async function logEvent(action, status="info", details={}){
  try{
    await db.from(CONFIG.tabelaAuditoria).insert({
      action,
      status,
      user_id: usuario?.id || null,
      user_name: usuario?.display_name || usuario?.username || null,
      user_role: usuario?.role || null,
      details,
      created_at: nowISO()
    });
  }catch(e){
    console.warn("Falha ao gravar auditoria:", e);
  }
}

async function logEventRaw(action, status, user, details={}){
  try{
    await db.from(CONFIG.tabelaAuditoria).insert({
      action,
      status,
      user_id: userId(user) || null,
      user_name: userNome(user),
      user_role: normalizeRole(user),
      details,
      created_at: nowISO()
    });
  }catch(e){
    console.warn("Falha ao gravar auditoria:", e);
  }
}

async function logHistory(registroId, action, beforeValue, afterValue, reason=null){
  try{
    await db.from(CONFIG.tabelaHistorico).insert({
      record_id: String(registroId),
      action,
      before_value: beforeValue,
      after_value: afterValue,
      reason,
      changed_by: usuario?.id || null,
      changed_by_name: usuario?.display_name || usuario?.username || null,
      created_at: nowISO()
    });
  }catch(e){
    console.warn("Falha ao gravar histórico:", e);
  }
}

async function requirePermission(perm, actionForAudit){
  if(HorizonSecurity.hasPermission(usuario, perm)) return true;

  await logEvent("PERMISSION_DENIED", "denied", {
    permission: perm,
    action: actionForAudit || perm,
    view: currentView
  });

  alert("Acesso negado. Esta tentativa foi registrada na auditoria.");
  return false;
}

async function carregarUsuarios(){
  const campos = f();
  const {data, error} = await db.from(CONFIG.tabelaUsuarios).select("*");

  if(error){
    setStatus("Erro ao carregar usuários da tabela public.usuarios: " + error.message, "error");
    console.error(error);
    return;
  }

  usuarios = (data || []).filter(u => {
    const ativo = u[campos.ativo || "ativo"];
    if(ativo === undefined || ativo === null) return true;
    return ["true","1","sim","ativo","active"].includes(String(ativo).toLowerCase());
  }).sort((a,b) => userNome(a).localeCompare(userNome(b)));

  refs.loginUsuario.innerHTML = usuarios.length
    ? usuarios.map(u => `<option value="${esc(userId(u))}">${esc(userNome(u))}</option>`).join("")
    : `<option value="">Nenhum usuário na tabela usuarios</option>`;

  resumoLogin();

  if(!usuarios.length){
    setStatus("Tabela usuarios carregou, mas não retornou usuários ativos.", "warn");
  }
}

function resumoLogin(){
  const u = usuarios.find(x => String(userId(x)) === String(refs.loginUsuario.value));

  if(!u){
    refs.loginResumo.innerHTML = "Nenhum usuário encontrado em public.usuarios.";
    return;
  }

  const role = normalizeRole(u);

  refs.loginResumo.innerHTML = `
    <strong>Perfil:</strong> ${esc(role)}<br>
    <strong>E-mail:</strong> ${esc(userEmail(u) || "—")}
  `;
}

async function login(e){
  e.preventDefault();
  clearLoginAlert();

  const campos = f();
  const u = usuarios.find(x => String(userId(x)) === String(refs.loginUsuario.value));
  const senha = refs.loginSenha.value;

  if(!u || !senha){
    alertLogin("Usuário ou senha inválidos.");
    return;
  }

  if(u[campos.lockedUntil] && new Date(u[campos.lockedUntil]) > new Date()){
    await logEventRaw("LOGIN_BLOCKED", "denied", u, { user_id: userId(u) });
    alertLogin("Usuário ou senha inválidos.");
    return;
  }

  let ok = false;
  const storedHash = u[campos.senhaHash];

  if(storedHash){
    ok = await HorizonSecurity.verifyPassword(senha, {
      hash: u[campos.senhaHash],
      salt: u[campos.senhaSalt],
      iterations: u[campos.senhaIteracoes]
    });
  } else {
    ok = String(senha) === String(u[campos.senhaAntiga || "senha"] || "");
  }

  if(!ok){
    const count = Number(u[campos.failedLoginCount] || 0) + 1;
    const patch = {
      [campos.failedLoginCount]: count,
      updated_at: nowISO()
    };

    if(count >= CONFIG.maxFalhasLogin){
      patch[campos.lockedUntil] = new Date(Date.now() + CONFIG.bloqueioMinutos * 60000).toISOString();
    }

    await db.from(CONFIG.tabelaUsuarios).update(patch).eq(campos.id, userId(u));
    await logEventRaw("LOGIN_FAIL", "denied", u, { failed_login_count: count });
    await carregarUsuarios();
    alertLogin("Usuário ou senha inválidos.");
    return;
  }

  const patch = {
    [campos.failedLoginCount]: 0,
    [campos.lockedUntil]: null,
    [campos.lastLoginAt]: nowISO(),
    updated_at: nowISO()
  };

  // Compatibilidade com EXE:
  // cria hash novo, mas NÃO apaga nem altera usuarios.senha.
  if(!storedHash){
    const hp = await HorizonSecurity.hashPassword(senha);
    patch[campos.senhaHash] = hp.hash;
    patch[campos.senhaSalt] = hp.salt;
    patch[campos.senhaAlgoritmo] = hp.algorithm;
    patch[campos.senhaIteracoes] = hp.iterations;
  }

  await db.from(CONFIG.tabelaUsuarios).update(patch).eq(campos.id, userId(u));

  usuario = HorizonSecurity.setSession({
    id: userId(u),
    username: userEmail(u) || userNome(u),
    display_name: userNome(u),
    role: normalizeRole(u)
  });

  await logEvent("LOGIN_OK", "success", {
    user_id: userId(u),
    migrated_hash_without_touching_senha: !storedHash
  });

  await carregarUsuarios();
  aplicarUsuario();
  hideLogin();
  await carregarRegistros();
}

function aplicarUsuario(){
  refs.userLabel.textContent = usuario ? `${usuario.display_name || usuario.username} · ${usuario.role}` : "Sem login";
  refs.kpiAcesso.textContent = usuario ? "OK" : "—";
  refs.kpiPerfil.textContent = usuario?.role || "perfil";
  refs.btnNovo.disabled = !usuario;
  lastActivity = Date.now();
  resetInactivityTimer();
}

async function logout(reason){
  await logEvent("LOGOUT", "success", { reason });
  HorizonSecurity.clearSession();
  usuario = null;
  registros = [];
  aplicarUsuario();
  render();
  showLogin();
  setStatus(reason, "warn");
}

function fillSelects(){
  refs.linha.innerHTML = CONFIG.linhas.map(l => `<option>${esc(l)}</option>`).join("");
  refs.motivo.innerHTML = CONFIG.motivos.map(m => `<option>${esc(m)}</option>`).join("");
}

async function carregarRegistros(){
  if(!usuario){
    showLogin();
    return;
  }

  const {data, error} = await db
    .from(CONFIG.tabelaRegistros)
    .select("*")
    .order("created_at", {ascending:false});

  if(error){
    setStatus("Erro ao carregar registros: " + error.message, "error");
    return;
  }

  registros = data || [];
  render();
  setStatus("Sistema carregado. Sessão expira após 5 minutos sem atividade.", "ok");
}

function render(){
  const ativos = registros.filter(r => !r.is_deleted);
  const lixeira = registros.filter(r => r.is_deleted);

  refs.kpiAbertos.textContent = ativos.filter(r => r.status === "EM ABERTURA").length;
  refs.kpiConcluidos.textContent = ativos.filter(r => r.status === "CONCLUÍDO" && String(r.data_registro).slice(0,10) === hojeISO()).length;
  refs.kpiLixeira.textContent = lixeira.length;

  if(currentView === "lixeira") renderRegistros(lixeira, true);
  else if(currentView === "auditoria") renderAuditoria();
  else if(currentView === "historico") renderHistorico();
  else renderRegistros(ativos, false);
}

function renderRegistros(lista, deleted=false){
  refs.viewTitle.textContent = deleted ? "Lixeira / Soft delete" : "Registros ativos";

  if(!lista.length){
    refs.tbodyRegistros.innerHTML = `<tr class="empty"><td colspan="11">Nenhum registro encontrado.</td></tr>`;
    refs.tableInfo.textContent = "Mostrando 0 registros";
    return;
  }

  refs.tbodyRegistros.innerHTML = lista.map(r => `
    <tr class="data" onclick="loadForm('${esc(r.id)}')">
      <td><span class="status ${deleted ? "deleted" : (r.status === "CONCLUÍDO" ? "done" : "open")}">${deleted ? "EXCLUÍDO" : esc(r.status || "ABERTO")}</span></td>
      <td>${esc(r.origem || CONFIG.origemPadrao)}</td>
      <td>${esc(dataBR(r.data_registro))}</td>
      <td>${esc(r.linha)}</td>
      <td>${esc(r.op || "—")}</td>
      <td>${esc(horaCurta(r.hora_inicio))}</td>
      <td>${esc(horaCurta(r.hora_fim))}</td>
      <td>${esc(calcTempo(r))}</td>
      <td>${esc(r.motivo || "—")}</td>
      <td>${esc(r.created_by_name || r.criado_por_nome || "—")}</td>
      <td>${esc(r.obs || "—")}</td>
    </tr>`).join("");

  refs.tableInfo.textContent = `Mostrando ${lista.length} registros`;
}

function calcTempo(r){
  if(!r.hora_inicio || !r.hora_fim) return "—";
  const [hi,mi] = String(r.hora_inicio).split(":").map(Number);
  const [hf,mf] = String(r.hora_fim).split(":").map(Number);
  let a = hi*60+mi;
  let b = hf*60+mf;
  if(b<a) b += 1440;
  const d = b-a;
  return `${String(Math.floor(d/60)).padStart(2,"0")}:${String(d%60).padStart(2,"0")}`;
}

async function changeView(view){
  closeMenu();

  if(view === "lixeira" && !(await requirePermission("registros.restaurar", "abrir_lixeira"))) return;
  if(view === "auditoria" && !(await requirePermission("auditoria.visualizar", "abrir_auditoria"))) return;
  if(view === "historico" && !(await requirePermission("historico.visualizar", "abrir_historico"))) return;

  currentView = view;
  await carregarRegistros();
}

function openMenu(){
  refs.sideMenu.classList.add("show");
  refs.shade.classList.add("show");
}

function closeMenu(){
  refs.sideMenu.classList.remove("show");
  refs.shade.classList.remove("show");
}

function requireLogin(){
  if(usuario) return true;
  showLogin();
  return false;
}

function novo(){
  if(!requireLogin()) return;

  if(!HorizonSecurity.hasPermission(usuario, "registros.criar")){
    requirePermission("registros.criar", "novo_registro");
    return;
  }

  selectedId = null;
  modoEdicaoId = null;

  refs.formTitle.textContent = "Novo Registro de Parada";
  refs.data.value = hojeBR();
  refs.inicio.value = horaAgora();
  refs.fim.value = "—";
  refs.linha.value = CONFIG.linhaPadrao;
  refs.op.value = "";
  refs.motivo.value = CONFIG.motivos[0];
  refs.obs.value = "";
  refs.suporte.checked = false;
  refs.statusForm.textContent = "Status: NOVO REGISTRO";

  refs.btnSalvar.classList.remove("hide");
  refs.btnEncerrar.classList.add("hide");
  refs.btnApagar.classList.add("hide");
  refs.btnRestaurar.classList.add("hide");

  setFormDisabled(false);
  clearFormAlert();
  abrirDrawer();
}

function loadForm(id){
  const r = registros.find(x => String(x.id) === String(id));
  if(!r) return;

  selectedId = r.id;
  modoEdicaoId = r.id;

  refs.formTitle.textContent = r.is_deleted ? "Registro na lixeira" : (r.status === "CONCLUÍDO" ? "Registro Concluído" : "Registro em Abertura");
  refs.data.value = dataBR(r.data_registro);
  refs.inicio.value = horaCurta(r.hora_inicio);
  refs.fim.value = horaCurta(r.hora_fim);
  refs.linha.value = r.linha || CONFIG.linhaPadrao;
  refs.op.value = r.op || "";
  refs.motivo.value = r.motivo || CONFIG.motivos[0];
  refs.obs.value = r.obs || "";
  refs.suporte.checked = !!r.suporte;
  refs.statusForm.textContent = `Status: ${r.is_deleted ? "EXCLUÍDO" : (r.status || "ABERTO")}`;

  refs.btnSalvar.classList.toggle("hide", !!r.is_deleted || !HorizonSecurity.hasPermission(usuario, "registros.editar"));
  refs.btnEncerrar.classList.toggle("hide", !!r.is_deleted || r.status === "CONCLUÍDO");
  refs.btnApagar.classList.toggle("hide", !!r.is_deleted || !HorizonSecurity.hasPermission(usuario, "registros.soft_delete"));
  refs.btnRestaurar.classList.toggle("hide", !r.is_deleted || !HorizonSecurity.hasPermission(usuario, "registros.restaurar"));

  setFormDisabled(!!r.is_deleted);
  clearFormAlert();
  refs.chars.textContent = `${refs.obs.value.length} caracteres`;
  abrirDrawer();
}

function abrirDrawer(){ refs.drawerBackdrop.classList.add("show"); }
function fecharDrawer(){ refs.drawerBackdrop.classList.remove("show"); }

function setFormDisabled(disabled){
  [refs.linha, refs.op, refs.motivo, refs.obs, refs.suporte].forEach(el => el.disabled = disabled);
}

async function salvarRegistro(e){
  e.preventDefault();

  if(!requireLogin()) return;

  const existente = modoEdicaoId ? registros.find(r => String(r.id) === String(modoEdicaoId)) : null;

  if(existente && !(await requirePermission("registros.editar", "editar_registro"))) return;

  if(!refs.motivo.value || !refs.obs.value.trim()){
    return alertForm(["Preencha motivo e observação."]);
  }

  const before = existente ? {...existente} : null;

  const payload = {
    origem: CONFIG.origemPadrao,
    linha: refs.linha.value,
    op: refs.op.value.trim() || null,
    motivo: refs.motivo.value,
    obs: refs.obs.value.trim(),
    suporte: refs.suporte.checked,
    updated_at: nowISO(),
    updated_by: usuario.id,
    updated_by_name: usuario.display_name || usuario.username
  };

  let result;

  if(existente){
    result = await db
      .from(CONFIG.tabelaRegistros)
      .update(payload)
      .eq("id", existente.id)
      .select()
      .single();
  } else {
    result = await db
      .from(CONFIG.tabelaRegistros)
      .insert({
        ...payload,
        status: "EM ABERTURA",
        data_registro: hojeISO(),
        hora_inicio: horaAgora(),
        hora_fim: null,
        is_deleted: false,
        created_at: nowISO(),
        created_by: usuario.id,
        created_by_name: usuario.display_name || usuario.username
      })
      .select()
      .single();
  }

  if(result.error){
    return alertForm(["Erro ao salvar: " + result.error.message]);
  }

  await logEvent(existente ? "REGISTRO_UPDATE" : "REGISTRO_CREATE", "success", { id: result.data.id });
  await logHistory(result.data.id, existente ? "REGISTRO_UPDATE" : "REGISTRO_CREATE", before, result.data);

  await carregarRegistros();
  fecharDrawer();
}

async function encerrarRegistro(){
  const r = registros.find(x => String(x.id) === String(modoEdicaoId));
  if(!r) return;

  if(!(await requirePermission("registros.finalizar", "finalizar_registro"))) return;

  if(!confirm(`Finalizar esta parada?\\n\\nLinha: ${r.linha}\\nMotivo: ${r.motivo}`)) return;

  const before = {...r};

  const patch = {
    status: "CONCLUÍDO",
    hora_fim: horaAgora(),
    finalized_at: nowISO(),
    finalized_by: usuario.id,
    finalized_by_name: usuario.display_name || usuario.username,
    updated_at: nowISO(),
    updated_by: usuario.id,
    updated_by_name: usuario.display_name || usuario.username
  };

  const {data, error} = await db
    .from(CONFIG.tabelaRegistros)
    .update(patch)
    .eq("id", r.id)
    .select()
    .single();

  if(error){
    return alertForm(["Erro ao finalizar: " + error.message]);
  }

  await logEvent("REGISTRO_FINISH", "success", { id: r.id });
  await logHistory(r.id, "REGISTRO_FINISH", before, data);

  await carregarRegistros();
  fecharDrawer();
}

async function reauthModal(title, message, includeReason=true){
  return new Promise(resolve => {
    refs.modalTitle.textContent = title;
    refs.modalText.textContent = message;
    refs.modalContent.innerHTML = `
      ${includeReason ? `<div class="field"><label>Motivo obrigatório</label><textarea id="criticalReason" placeholder="Descreva o motivo"></textarea></div>` : ""}
      <div class="field"><label>Digite sua senha novamente</label><input class="input" id="criticalPassword" type="password"></div>
    `;

    refs.genericModal.classList.add("show");

    refs.modalCancel.onclick = () => {
      refs.genericModal.classList.remove("show");
      resolve(null);
    };

    refs.modalOk.onclick = async () => {
      const reason = includeReason ? document.getElementById("criticalReason").value.trim() : "";
      const password = document.getElementById("criticalPassword").value;

      if(includeReason && !reason) return alert("Motivo obrigatório.");
      if(!password) return alert("Senha obrigatória.");

      const full = usuarios.find(u => String(userId(u)) === String(usuario.id)) || await getCurrentUserFull();

      let ok = false;

      if(full?.[f().senhaHash]){
        ok = await HorizonSecurity.verifyPassword(password, {
          hash: full[f().senhaHash],
          salt: full[f().senhaSalt],
          iterations: full[f().senhaIteracoes]
        });
      } else {
        ok = String(password) === String(full?.[f().senhaAntiga || "senha"] || "");
      }

      if(!ok){
        await logEvent("CRITICAL_REAUTH_FAIL", "denied", { title });
        return alert("Usuário ou senha inválidos.");
      }

      refs.genericModal.classList.remove("show");
      resolve({reason, passwordOk:true});
    };
  });
}

async function getCurrentUserFull(){
  const {data} = await db
    .from(CONFIG.tabelaUsuarios)
    .select("*")
    .eq(f().id, usuario.id)
    .single();

  return data;
}

async function apagarRegistro(){
  const r = registros.find(x => String(x.id) === String(modoEdicaoId));
  if(!r) return;

  if(!(await requirePermission("registros.soft_delete", "excluir_registro"))) return;

  if(!confirm(`Confirmar exclusão segura?\\n\\nLinha: ${r.linha}\\nMotivo: ${r.motivo}\\n\\nO registro irá para a lixeira.`)) return;

  const auth = await reauthModal("Exclusão segura", "Para excluir, informe motivo e senha. O registro irá para a lixeira.", true);
  if(!auth) return;

  const before = {...r};

  const patch = {
    is_deleted: true,
    deleted_at: nowISO(),
    deleted_by: usuario.id,
    deleted_by_name: usuario.display_name || usuario.username,
    deleted_reason: auth.reason,
    updated_at: nowISO(),
    updated_by: usuario.id,
    updated_by_name: usuario.display_name || usuario.username
  };

  const {data, error} = await db
    .from(CONFIG.tabelaRegistros)
    .update(patch)
    .eq("id", r.id)
    .select()
    .single();

  if(error){
    return alertForm(["Erro ao excluir: " + error.message]);
  }

  await logEvent("REGISTRO_SOFT_DELETE", "success", { id: r.id, reason: auth.reason });
  await logHistory(r.id, "REGISTRO_SOFT_DELETE", before, data, auth.reason);

  await carregarRegistros();
  fecharDrawer();
}

async function restaurarRegistro(){
  const r = registros.find(x => String(x.id) === String(modoEdicaoId));
  if(!r) return;

  if(!(await requirePermission("registros.restaurar", "restaurar_registro"))) return;

  if(!confirm(`Restaurar registro da lixeira?\\n\\nLinha: ${r.linha}\\nMotivo: ${r.motivo}`)) return;

  const auth = await reauthModal("Restaurar registro", "Informe motivo e senha para restaurar.", true);
  if(!auth) return;

  const before = {...r};

  const patch = {
    is_deleted: false,
    restored_at: nowISO(),
    restored_by: usuario.id,
    restored_by_name: usuario.display_name || usuario.username,
    restored_reason: auth.reason,
    updated_at: nowISO(),
    updated_by: usuario.id,
    updated_by_name: usuario.display_name || usuario.username
  };

  const {data, error} = await db
    .from(CONFIG.tabelaRegistros)
    .update(patch)
    .eq("id", r.id)
    .select()
    .single();

  if(error){
    return alertForm(["Erro ao restaurar: " + error.message]);
  }

  await logEvent("REGISTRO_RESTORE", "success", { id: r.id, reason: auth.reason });
  await logHistory(r.id, "REGISTRO_RESTORE", before, data, auth.reason);

  await carregarRegistros();
  fecharDrawer();
}

async function renderAuditoria(){
  refs.viewTitle.textContent = "Auditoria";

  const {data, error} = await db
    .from(CONFIG.tabelaAuditoria)
    .select("*")
    .order("created_at", {ascending:false})
    .limit(100);

  if(error){
    refs.tbodyRegistros.innerHTML = `<tr class="empty"><td colspan="11">Erro ao carregar auditoria: ${esc(error.message)}</td></tr>`;
    return;
  }

  refs.tbodyRegistros.innerHTML = `<tr><td colspan="11">${(data||[]).map(e => `
    <div class="auditItem">
      <strong>${esc(e.action)}</strong> · ${esc(e.status)} · ${esc(e.user_name || "sem usuário")} · ${esc(e.created_at)}
      <code>${esc(JSON.stringify(e.details || {}, null, 2))}</code>
    </div>`).join("") || "Sem auditoria."}</td></tr>`;

  refs.tableInfo.textContent = `Mostrando ${(data||[]).length} eventos`;
}

async function renderHistorico(){
  refs.viewTitle.textContent = "Histórico antes/depois";

  const {data, error} = await db
    .from(CONFIG.tabelaHistorico)
    .select("*")
    .order("created_at", {ascending:false})
    .limit(80);

  if(error){
    refs.tbodyRegistros.innerHTML = `<tr class="empty"><td colspan="11">Erro ao carregar histórico: ${esc(error.message)}</td></tr>`;
    return;
  }

  refs.tbodyRegistros.innerHTML = `<tr><td colspan="11">${(data||[]).map(h => `
    <div class="auditItem">
      <strong>${esc(h.action)}</strong> · ${esc(h.changed_by_name || "—")} · ${esc(h.created_at)}<br>
      <b>Motivo:</b> ${esc(h.reason || "—")}
      <code>ANTES: ${esc(JSON.stringify(h.before_value || {}, null, 2))}</code>
      <code>DEPOIS: ${esc(JSON.stringify(h.after_value || {}, null, 2))}</code>
    </div>`).join("") || "Sem histórico."}</td></tr>`;

  refs.tableInfo.textContent = `Mostrando ${(data||[]).length} históricos`;
}

async function backupView(){
  closeMenu();

  if(!(await requirePermission("backup.exportar", "abrir_backup"))) return;

  refs.viewTitle.textContent = "Backup / Restauração";

  refs.tbodyRegistros.innerHTML = `
    <tr><td colspan="11">
      <div class="auditItem">
        <strong>Backup JSON</strong><br>
        Exporta registros, auditoria e histórico. Restauração somente Admin Master.
        <br><br>
        <button class="smallbtn" onclick="exportarBackup()">Exportar backup JSON</button>
        <button class="smallbtn" onclick="importarBackupClick()">Restaurar backup JSON</button>
        <input id="backupFile" type="file" accept=".json" class="hide" onchange="restaurarBackup(event)">
      </div>
    </td></tr>`;

  refs.tableInfo.textContent = "Backup";
}

window.exportarBackup = async function(){
  if(!(await requirePermission("backup.exportar", "exportar_backup"))) return;

  const regs = await db.from(CONFIG.tabelaRegistros).select("*");
  const aud = await db.from(CONFIG.tabelaAuditoria).select("*").limit(5000);
  const hist = await db.from(CONFIG.tabelaHistorico).select("*").limit(5000);

  const payload = {
    exported_at: nowISO(),
    exported_by: usuario,
    registros: regs.data || [],
    auditoria: aud.data || [],
    historico: hist.data || []
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `horizon_backup_${new Date().toISOString().replace(/[:.]/g,"-")}.json`;
  a.click();
  URL.revokeObjectURL(a.href);

  await logEvent("BACKUP_EXPORT", "success", { registros: payload.registros.length });
};

window.importarBackupClick = async function(){
  if(!(await requirePermission("backup.restaurar", "restaurar_backup"))) return;
  document.getElementById("backupFile").click();
};

window.restaurarBackup = async function(event){
  if(!HorizonSecurity.hasPermission(usuario, "backup.restaurar")){
    await requirePermission("backup.restaurar", "restaurar_backup");
    return;
  }

  const file = event.target.files[0];
  if(!file) return;

  if(!confirm("Restaurar backup JSON? Esta ação é crítica e somente Admin Master deve executar.")) return;

  const auth = await reauthModal("Restauração de backup", "Admin Master: informe motivo e senha para restaurar o backup.", true);
  if(!auth) return;

  const json = JSON.parse(await file.text());
  const regs = Array.isArray(json.registros) ? json.registros : [];

  if(!regs.length) return alert("Backup não contém registros.");

  const {error} = await db.from(CONFIG.tabelaRegistros).upsert(regs);

  if(error) return alert("Erro ao restaurar backup: " + error.message);

  await logEvent("BACKUP_RESTORE", "success", { registros: regs.length, reason: auth.reason });
  alert("Backup restaurado.");
  await carregarRegistros();
};
