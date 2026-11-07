# Mapeamento dos referenciais de GP

Este documento liga cada conceito dos referenciais ao lugar do código onde ele aparece. É um documento vivo: cada funcionalidade nova deve atualizar a tabela.

> ⚠️ Os nomes de domínios, práticas e princípios devem ser conferidos nas edições oficiais (PMBOK® Guide 8ª ed., PRINCE2® 7, guia PM4R do BID) antes de serem usados em avaliação.

| Conceito | PMBOK 8 | PRINCE2 7 | PM4R | Onde no código |
|---|---|---|---|---|
| Ciclo de vida em fases | Iniciação → Encerramento | Processos (do início ao encerramento) | Fases do ciclo do projeto | `domain/project.py` · `ProjectPhase` |
| Justificativa do projeto | Valor / benefícios | Justificativa contínua (*business case*) | Foco em resultados | `Project.expected_benefits` |
| Estágios e tolerâncias | Linhas de base e controle | Gestão por estágios e por exceção | Cronograma e orçamento | `domain/project.py` · `Stage` |
| Riscos | Domínio de riscos | Prática de riscos | Matriz de riscos | `domain/risk.py` |
| Monitoramento | Medição de desempenho | Relatório de exceção / progresso | Monitoramento e controle | `agents/risk_monitor.py` |

## Backlog de aderência

- [ ] Partes interessadas (matriz poder × interesse)
- [ ] EAP / estrutura analítica e produtos (PRINCE2: *product-based planning*)
- [ ] Valor agregado (CPI/SPI)
- [ ] Matriz de comunicação (PM4R)
- [ ] Lições aprendidas no encerramento
