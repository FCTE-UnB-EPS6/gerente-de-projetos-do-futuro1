# Como contribuir

1. **Issue primeiro.** Toda mudança nasce de uma issue com critérios de aceitação.
2. **Branch curta** a partir da `main`: `feat/42-registro-de-riscos`. Integre em até 2–3 dias (trunk-based).
3. **Commits** no padrão Conventional Commits:
   `feat(riscos): calcula nível pelo score P×I`
4. **Antes do PR:** rode `make check` (lint + tipos + testes).
5. **PR** pequeno (idealmente < 400 linhas), com o template preenchido.
6. **Merge:** *squash*, após CI verde e aprovação do CODEOWNER.

## Uso de IA

O uso de assistentes de IA (Claude, Copilot, Codex) é incentivado. As regras para agentes estão em [CLAUDE.md](CLAUDE.md). Quem abre o PR responde pelo código, tenha sido escrito por humano ou por IA.
