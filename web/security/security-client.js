/* Horizon Security Client
   Somente UX. A segurança real precisa estar no backend/API.
*/
const HorizonSecurity = (() => {
  const TOKEN_KEY = 'horizon_access_token';
  let currentUser = null;
  let currentPermissions = {};

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      clearToken();
      showSessionExpired();
      throw new Error('Sessão expirada.');
    }
    if (res.status === 403) {
      showToast('Ação bloqueada: seu perfil não tem permissão.', 'warning');
      throw new Error('Sem permissão.');
    }
    if (res.status === 423) {
      showToast('Sistema em modo protegido. Edição bloqueada.', 'danger');
      throw new Error('Modo protegido.');
    }
    if (!res.ok) {
      let msg = 'Erro na API.';
      try { msg = (await res.json()).detail || msg; } catch(e) {}
      throw new Error(msg);
    }
    return res.json();
  }

  async function login(login, password) {
    const data = await apiFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ login, password })
    });
    setToken(data.access_token);
    await loadMe();
    return data;
  }

  async function logout() {
    try { await apiFetch('/api/auth/logout', { method: 'POST', body: '{}' }); } catch(e) {}
    clearToken();
    window.location.href = '/login.html';
  }

  async function loadMe() {
    const data = await apiFetch('/api/auth/me');
    currentUser = data.user;
    currentPermissions = data.permissions || {};
    applyUserToUI();
    applyPermissionsToUI();
    return data;
  }

  function hasPermission(permission) {
    return !!currentPermissions[permission];
  }

  function applyUserToUI() {
    document.querySelectorAll('[data-current-user]').forEach(el => {
      el.textContent = currentUser ? `${currentUser.display_name || currentUser.username} (${currentUser.role})` : '';
    });
  }

  function applyPermissionsToUI() {
    document.querySelectorAll('[data-permission]').forEach(el => {
      const perm = el.getAttribute('data-permission');
      el.style.display = hasPermission(perm) ? '' : 'none';
    });
  }

  async function reauth(action) {
    const password = window.prompt('Confirme sua senha para continuar:');
    if (!password) throw new Error('Ação cancelada.');
    const data = await apiFetch('/api/auth/reauth', {
      method: 'POST',
      body: JSON.stringify({ password, action })
    });
    return data.reauth_token;
  }

  function confirmCritical(message) {
    return window.confirm(message || 'Confirma esta ação crítica?');
  }

  function showToast(message, type = 'info') {
    let box = document.querySelector('#horizon-toast');
    if (!box) {
      box = document.createElement('div');
      box.id = 'horizon-toast';
      document.body.appendChild(box);
    }
    box.className = `horizon-toast ${type}`;
    box.textContent = message;
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 4500);
  }

  function showSessionExpired() {
    showToast('Sua sessão expirou. Faça login novamente.', 'warning');
    setTimeout(() => { window.location.href = '/login.html'; }, 1200);
  }

  function enableDevToolsBarrier() {
    // Barreira leve. Não é segurança real.
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('keydown', e => {
      const key = (e.key || '').toLowerCase();
      if (key === 'f12' || (e.ctrlKey && e.shiftKey && ['i','j','c'].includes(key)) || (e.ctrlKey && key === 'u')) {
        e.preventDefault();
        showToast('DevTools bloqueado neste ambiente.', 'warning');
      }
    });
  }

  async function init({ devtoolsBarrier = false } = {}) {
    if (devtoolsBarrier) enableDevToolsBarrier();
    if (getToken()) {
      try { await loadMe(); } catch(e) { clearToken(); }
    }
  }

  return { init, login, logout, apiFetch, loadMe, hasPermission, reauth, confirmCritical, showToast };
})();
