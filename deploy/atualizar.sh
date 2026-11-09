#!/usr/bin/env bash
# Busca no GHCR as versões marcadas para homologação e produção e atualiza só o que mudou.
# Executado a cada 2 minutos pelo systemd (gpf-atualizar.timer). Pode ser rodado à mão.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

log() { echo "$(date -Iseconds) $*"; }

for servico in homologacao producao; do
  antes="$(docker compose images -q "$servico" 2>/dev/null || true)"
  if ! docker compose pull --quiet "$servico"; then
    # A tag ainda não existe (por exemplo, produção antes da primeira aprovação): não é erro.
    log "$servico: nenhuma imagem disponível no GHCR ainda"
    continue
  fi
  docker compose up -d --remove-orphans "$servico"
  depois="$(docker compose images -q "$servico")"
  if [[ "$antes" != "$depois" ]]; then
    revisao="$(docker inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "gpf-$servico" 2>/dev/null || echo '?')"
    log "$servico: atualizado para ${revisao:0:7}"
  fi
done

docker image prune -f --filter "until=168h" > /dev/null
