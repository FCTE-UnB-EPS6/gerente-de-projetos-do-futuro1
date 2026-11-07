# Instruções para agentes de IA (Claude, Codex, Copilot)

Este arquivo vale para qualquer agente que trabalhe neste repositório. `AGENTS.md` aponta para cá.

## Contexto
- Projeto: Gerente de Projetos do Futuro (GPF). É um app de gerência de projetos com IA agêntica, aderente a PMBOK 8, PRINCE2 7 e PM4R.
- Idioma: documentação, issues e PRs em **português**. Código (nomes de variáveis e funções) em **inglês**.

## Comandos
- Instalar: `pip install -e ".[dev]"`
- Testes: `make test` (pytest com cobertura mínima de 80%)
- Lint/format: `make lint` / `make format` (ruff)
- Tipos: `make typecheck` (mypy, modo estrito em `src/`)
- Rodar API: `make run`

## Regras
1. Nunca faça commit direto na `main`. Use branch + PR.
2. Todo código novo precisa de teste. Não reduza a cobertura.
3. `src/gpf/domain/` não importa FastAPI, banco de dados nem SDK de LLM. O domínio é puro.
4. Agentes de IA implementam os contratos de `src/gpf/agents/base.py`. Toda ação de agente que altere dados exige aprovação humana (*human-in-the-loop*).
5. Nunca grave segredos no código. Use variáveis de ambiente (veja `.env.example`).
6. Commits no padrão Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`).
7. Decisões de arquitetura relevantes viram um ADR em `docs/adr/`.
