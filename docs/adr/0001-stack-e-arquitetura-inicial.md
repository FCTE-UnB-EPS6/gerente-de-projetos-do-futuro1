# ADR 0001 — Stack e arquitetura inicial

- **Status:** aceito
- **Data:** 2026-11-07

## Contexto

O GPF precisa combinar regras de gerência de projetos, agentes de IA e ML. Também precisa ser desenvolvido por várias equipes de estudantes, com segurança verificável desde o início.

## Decisão

- **Python 3.12 + FastAPI.** É o ecossistema dominante em IA/ML e tem tipagem forte com Pydantic.
- **Domínio puro em camadas** (`domain` ← `agents` ← `api`).
- **Human-in-the-loop obrigatório.** Agentes só produzem propostas.
- **Trunk-based development.** Branches curtas, PR com CI e CODEOWNERS, *squash merge*.
- **DevSecOps na CI:** ruff, mypy estrito, pytest (≥ 80%), CodeQL, Gitleaks, pip-audit, Trivy e Dependabot.
- **Dev Container** para um ambiente idêntico entre alunos (Codespaces).

## Consequências

- As regras de GP ficam testáveis sem infraestrutura.
- Agentes baseados em LLM podem ser trocados ou avaliados isoladamente.
- A CI mais rigorosa aumenta um pouco o tempo dos PRs, em troca de qualidade e segurança mensuráveis.
