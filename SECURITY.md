# Política de segurança

## Como relatar uma vulnerabilidade

**Não abra issue pública.** Use **Security → Report a vulnerability** neste repositório (relato privado) ou contate o mantenedor diretamente.

Inclua: descrição, passos para reproduzir, impacto estimado e, se possível, uma sugestão de correção. Responderemos em até 5 dias úteis.

## Controles adotados

- Varredura de segredos (Gitleaks) no pre-commit e na CI
- SAST com CodeQL (`security-extended`)
- Auditoria de dependências (pip-audit) e atualizações automáticas (Dependabot)
- Scan da imagem Docker (Trivy) e container executando sem root
- Revisão obrigatória via CODEOWNERS e proteção da branch `main`
- Agentes de IA não executam alterações sem aprovação humana
