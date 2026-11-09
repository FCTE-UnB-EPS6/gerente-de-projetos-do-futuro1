# ADR 0002 — Implantação no servidor da universidade por promoção de tags

- **Status:** aceito
- **Data:** 2026-11-09

## Contexto

A produção do GPF vai rodar num servidor da universidade, atrás do firewall institucional. O repositório é público, e o projeto quer uma etapa de homologação com aprovação humana antes da produção.

## Opções consideradas

1. **Deploy por SSH a partir do GitHub Actions.** Exige abrir porta para a internet e guardar uma chave SSH com acesso ao servidor como segredo do GitHub.
2. **Runner self-hosted no servidor.** Não abre porta, mas um runner num repositório público pode executar código de PRs de terceiros se for mal configurado.
3. **Promoção de tags no GHCR, com o servidor buscando as imagens (pull-based).** O GitHub só remarca imagens; o servidor faz `docker compose pull` periodicamente.

## Decisão

Opção 3. O fluxo é o seguinte:

- Todo merge na `main` com CI verde publica a imagem `:<sha>` e a promove para `:homologacao`.
- A promoção para `:producao` roda no ambiente `producao` do GitHub, que exige aprovação de um revisor.
- No servidor, um timer do systemd roda `deploy/atualizar.sh` a cada 2 minutos.
- O rollback é uma remarcação de tag pelo workflow manual **Promover versão (rollback)**.

## Consequências

- Nenhuma porta de entrada aberta e nenhuma credencial do servidor no GitHub.
- A aprovação de produção fica registrada no GitHub, com autor e horário.
- Uma nova versão leva até 2 minutos para entrar no ar depois da promoção.
- O GitHub não verifica a saúde do ambiente depois da troca. Essa verificação fica com o healthcheck do container e com o teste manual em homologação antes da aprovação.
- O pacote no GHCR precisa ser público, ou o servidor precisa de um token de leitura.
