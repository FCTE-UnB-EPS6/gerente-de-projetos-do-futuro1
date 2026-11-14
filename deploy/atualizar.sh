#!/usr/bin/env bash
# Atualiza a API no DATEN para uma tag da imagem, com verificação de saúde e rollback.
# Uso (no DATEN):  /srv/gpf/atualizar.sh <sha-do-commit|latest>
set -euo pipefail

cd "$(dirname "$0")"
NEW_TAG="${1:?informe a tag (SHA do commit ou latest)}"
OLD_TAG="$(grep -E '^GPF_IMAGE_TAG=' .env | cut -d= -f2-)"

set_tag() { sed -i "s/^GPF_IMAGE_TAG=.*/GPF_IMAGE_TAG=$1/" .env; }

echo "→ Atualizando de '${OLD_TAG}' para '${NEW_TAG}'"
set_tag "$NEW_TAG"
docker compose --env-file .env pull api
docker compose --env-file .env up -d api

for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    echo "✓ GPF saudável na tag ${NEW_TAG}"
    docker image prune -f >/dev/null
    exit 0
  fi
  sleep 2
done

echo "✗ /health não respondeu. Voltando para '${OLD_TAG}'." >&2
docker compose --env-file .env logs --tail 50 api >&2 || true
set_tag "$OLD_TAG"
docker compose --env-file .env up -d api
exit 1
