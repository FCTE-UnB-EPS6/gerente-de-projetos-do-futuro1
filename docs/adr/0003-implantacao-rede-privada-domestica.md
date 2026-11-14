# ADR 0003 — Implantação em rede privada doméstica

- **Status:** proposto
- **Data:** 2026-11-14

## Contexto

O mantenedor dispõe de um PC Linux (DATEN, SSD de 1 TB, já com n8n e PostgreSQL endurecidos)
e de um Mac Mini. Quer operar o GPF em produção em casa, sem expor serviços à internet.

## Decisão

- **DATEN** é o servidor de produção; **Mac Mini** é a estação de desenvolvimento e de treino dos modelos.
- Acesso exclusivamente pela **tailnet (Tailscale/WireGuard)**; nenhum *port forwarding* no roteador.
- A API escuta só em `127.0.0.1`; o `tailscale serve` publica HTTPS com certificado válido na tailnet.
- Container endurecido: usuário sem privilégio (10001), sistema de arquivos somente leitura,
  `cap_drop: ALL`, `no-new-privileges`, limites de memória, CPU e processos; modelo montado como somente leitura.
- Entrega por *pull*: o DATEN baixa do GHCR a imagem gerada pela esteira; atualização com teste de saúde e rollback.
- Rotas `/ml/*` protegidas por token (defesa em profundidade, mesmo dentro da rede privada).
- Sem *runner* auto-hospedado: o repositório é público.

## Consequências

- O mesmo `deploy/docker-compose.yml` serve ao servidor da universidade, mudando só a forma de acesso.
- Disponibilidade depende da energia e da internet de casa; sem SLA. Adequado para uso pessoal,
  pilotos e homologação, não para serviço crítico a terceiros.
- Backups (`/srv/gpf` e banco) passam a ser responsabilidade do mantenedor (regra 3-2-1).
