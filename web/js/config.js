/* CONFIGURAÇÃO PÚBLICA DO HORIZON
   A anon key do Supabase é pública por natureza. NUNCA coloque service_role aqui.
   Copie sua URL e sua anon/public key do Supabase.
*/
window.HORIZON_CONFIG = {
  supabaseUrl: "COLE_AQUI_SUA_SUPABASE_URL",
  supabaseAnonKey: "COLE_AQUI_SUA_SUPABASE_ANON_KEY",

  tabelaRegistros: "downtime_pth_wave",
  tabelaUsuarios: "horizon_users",
  tabelaAuditoria: "horizon_security_events",
  tabelaHistorico: "horizon_record_history",

  origemPadrao: "PTH/WAVE",
  linhas: ["PTH/Wave 1", "PTH/Wave 2"],
  linhaPadrao: "PTH/Wave 1",
  motivos: [
    "Setup",
    "Falta de material",
    "Qualidade",
    "Parada por Processo",
    "Manutenção",
    "Aguardando suporte",
    "Outro"
  ],

  sessaoInatividadeMs: 5 * 60 * 1000,
  maxFalhasLogin: 5,
  bloqueioMinutos: 15
};
