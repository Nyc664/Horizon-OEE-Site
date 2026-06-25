/* CONFIGURAÇÃO PÚBLICA DO HORIZON
   Usa GitHub Pages + Supabase.
   Use somente Publishable/anon key. NUNCA use secret key ou service_role aqui.
*/
window.HORIZON_CONFIG = {
  supabaseUrl: "https://abmlvlkkflxzvcciwawz.supabase.co",
  supabaseAnonKey: "sb_publishable_QpuOFGCQUZKG2LGV027sHA_dxSw5McV",

  tabelaRegistros: "downtime_pth_wave",
  tabelaUsuarios: "usuarios",
  tabelaAuditoria: "horizon_security_events",
  tabelaHistorico: "horizon_record_history",

  usuarioCampos: {
    id: "id",
    nome: "nome",
    email: "email",
    senhaAntiga: "senha",
    setor: "setor",
    role: "role",
    ativo: "ativo",

    senhaHash: "senha_hash",
    senhaSalt: "senha_salt",
    senhaAlgoritmo: "senha_algoritmo",
    senhaIteracoes: "senha_iteracoes",
    failedLoginCount: "failed_login_count",
    lockedUntil: "locked_until",
    lastLoginAt: "last_login_at"
  },

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
