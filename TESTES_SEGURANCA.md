# Checklist de Testes de Segurança — Horizon OEE Web

## 1. Login

- [ ] Login válido entra no sistema.
- [ ] Login inválido mostra mensagem genérica.
- [ ] Senha errada registra auditoria.
- [ ] Após várias falhas, usuário é bloqueado.
- [ ] Usuário inativo não consegue entrar.

## 2. Sessão

- [ ] Sem token não acessa rota protegida.
- [ ] Token inválido retorna 401.
- [ ] Sessão expirada retorna 401.
- [ ] Logout revoga token.
- [ ] Após logout, token antigo não funciona.

## 3. Permissões

- [ ] Operador não consegue editar registro pela tela.
- [ ] Operador não consegue editar via F12/fetch manual.
- [ ] Operador não consegue excluir via API manual.
- [ ] Admin consegue editar.
- [ ] Admin consegue soft delete.
- [ ] Admin não consegue apagar definitivamente.
- [ ] Admin Master consegue apagar definitivamente.
- [ ] Toda tentativa sem permissão aparece na auditoria.

## 4. Soft delete/lixeira

- [ ] Excluir registro não apaga do banco imediatamente.
- [ ] Registro sai da visão principal.
- [ ] Registro aparece na lixeira.
- [ ] Motivo de exclusão é obrigatório.
- [ ] Quem excluiu fica gravado.
- [ ] Data/hora da exclusão fica gravada.
- [ ] Restaurar exige permissão.
- [ ] Restaurar registra motivo e usuário.

## 5. Auditoria

- [ ] Login aparece na auditoria.
- [ ] Falha de login aparece na auditoria.
- [ ] Edição aparece na auditoria.
- [ ] Exclusão aparece na auditoria.
- [ ] Restauração aparece na auditoria.
- [ ] Exportação aparece na auditoria.
- [ ] Tentativa sem permissão aparece como denied.

## 6. Histórico antes/depois

- [ ] Ao editar, salva antes.
- [ ] Ao editar, salva depois.
- [ ] Mostra campos alterados.
- [ ] Mostra quem editou.
- [ ] Mostra data/hora.

## 7. Backup

- [ ] Backup é criado ao iniciar.
- [ ] Backup manual funciona.
- [ ] Backup tem SHA-256.
- [ ] Backup aparece na tabela `security_backups`.
- [ ] Backup é criado antes de ação crítica, se configurado.

## 8. Integridade

- [ ] `PRAGMA integrity_check` retorna ok.
- [ ] Checksum inicial é salvo.
- [ ] Alteração manual suspeita gera divergência.
- [ ] Divergência ativa modo protegido.

## 9. Modo protegido

- [ ] Modo protegido bloqueia edição.
- [ ] Modo protegido bloqueia exclusão.
- [ ] Modo protegido permite visualização básica.
- [ ] Admin Master consegue desativar com motivo.
- [ ] Ativação/desativação fica na auditoria.

## 10. F12/DevTools

- [ ] F12 pode até mostrar HTML/JS, mas não mostra segredo.
- [ ] Não existe senha no frontend.
- [ ] Não existe Service Role no frontend.
- [ ] Não existe regra crítica somente no JS.
- [ ] Chamada manual para API sem permissão retorna 403.

## 11. Supabase futuro

- [ ] Service Role não aparece no projeto frontend.
- [ ] `.env.example` não contém chave real.
- [ ] RLS planejado para tabelas críticas.
- [ ] Ações críticas continuam passando pelo backend.
