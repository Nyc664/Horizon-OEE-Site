/* Horizon Static Security
   Sem backend: isto é uma proteção prática para GitHub Pages + Supabase.
   Para segurança industrial real contra usuário malicioso, usar backend ou RLS forte.
*/
const HorizonSecurity = (() => {
  const enc = new TextEncoder();

  function bytesToBase64(bytes){
    let bin = "";
    bytes.forEach(b => bin += String.fromCharCode(b));
    return btoa(bin);
  }

  function base64ToBytes(base64){
    const bin = atob(base64);
    return Uint8Array.from(bin, c => c.charCodeAt(0));
  }

  async function pbkdf2Hash(password, saltBase64, iterations = 150000){
    const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
    const bits = await crypto.subtle.deriveBits(
      { name: "PBKDF2", salt: base64ToBytes(saltBase64), iterations, hash: "SHA-256" },
      keyMaterial,
      256
    );
    return bytesToBase64(new Uint8Array(bits));
  }

  async function hashPassword(password){
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const saltBase64 = bytesToBase64(salt);
    const iterations = 150000;
    const hash = await pbkdf2Hash(password, saltBase64, iterations);
    return { algorithm: "PBKDF2-SHA256", iterations, salt: saltBase64, hash };
  }

  async function verifyPassword(password, stored){
    if(!stored || !stored.hash || !stored.salt) return false;
    const iterations = Number(stored.iterations || 150000);
    const hash = await pbkdf2Hash(password, stored.salt, iterations);
    return timingSafeEqual(hash, stored.hash);
  }

  function timingSafeEqual(a,b){
    if(typeof a !== "string" || typeof b !== "string") return false;
    let diff = a.length ^ b.length;
    const len = Math.max(a.length, b.length);
    for(let i=0;i<len;i++) diff |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
    return diff === 0;
  }

  function sessionKey(){ return "horizon_static_session"; }

  function setSession(user){
    const safeUser = {
      id: user.id,
      username: user.username,
      display_name: user.display_name,
      role: user.role,
      login_at: new Date().toISOString()
    };
    sessionStorage.setItem(sessionKey(), JSON.stringify(safeUser));
    return safeUser;
  }

  function getSession(){
    try { return JSON.parse(sessionStorage.getItem(sessionKey()) || "null"); }
    catch(e){ return null; }
  }

  function clearSession(){ sessionStorage.removeItem(sessionKey()); }

  function rolePerms(role){
    const r = String(role || "").toUpperCase();
    const base = ["registros.visualizar","registros.criar"];
    if(r === "OPERADOR") return new Set([...base, "registros.finalizar"]);
    if(r === "ADMIN") return new Set([...base, "registros.editar","registros.finalizar","registros.soft_delete","registros.restaurar","auditoria.visualizar","historico.visualizar","backup.exportar"]);
    if(r === "ADMIN_MASTER") return new Set([...base, "registros.editar","registros.finalizar","registros.soft_delete","registros.restaurar","auditoria.visualizar","historico.visualizar","backup.exportar","backup.restaurar","usuarios.admin"]);
    return new Set([]);
  }

  function hasPermission(user, perm){
    if(!user) return false;
    return rolePerms(user.role).has(perm);
  }

  return { hashPassword, verifyPassword, setSession, getSession, clearSession, hasPermission, rolePerms };
})();
