# Arquitetura

## Camadas

```
┌──────────────────────────────────────────┐
│ api/       FastAPI — HTTP, validação     │
├──────────────────────────────────────────┤
│ agents/    Agentes de IA — analisam e    │
│            PROPÕEM (human-in-the-loop)   │
├──────────────────────────────────────────┤
│ domain/    Regras de GP puras: projeto,  │
│            fases, estágios, riscos       │
└──────────────────────────────────────────┘
```

As dependências apontam sempre para baixo. O domínio não conhece nem a API nem os agentes.

## Princípios

1. **Domínio puro e testável.** As regras de PMBOK, PRINCE2 e PM4R vivem em `domain/`, sem framework, banco de dados nem LLM.
2. **Agentes propõem, humanos decidem.** Todo agente implementa `Agent.analyze()` e devolve `AgentProposal`. A proposta só tem efeito depois de `approve()`, com um revisor identificado.
3. **Determinístico antes de generativo.** Cada agente começa com regras explícitas (ex.: `RiskMonitorAgent`). O LLM entra para enriquecer: redigir relatórios, sugerir respostas a riscos, resumir o progresso.
4. **Segurança desde o commit.** Segredos, SAST, dependências e imagem são verificados automaticamente (veja `SECURITY.md`).

## Próximos passos sugeridos

- Persistência (PostgreSQL + SQLAlchemy) em `infra/`, atrás de repositórios definidos no domínio
- Agente de relatório de progresso com LLM (Claude), com avaliação automática (*evals*) na CI
- Front-end (painel do projeto)
- Observabilidade: logs estruturados e trilha de auditoria das decisões humanas
