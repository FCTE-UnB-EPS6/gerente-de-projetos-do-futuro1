#!/usr/bin/env bash
# Treina o modelo no Mac Mini e publica no DATEN pela tailnet, fixando o SHA-256.
# Uso (no Mac Mini, na raiz do repositório, com o venv ativo):
#   deploy/publicar-modelo.sh                     # base sintética (demonstração)
#   deploy/publicar-modelo.sh dados/historico.csv # base real
# Variáveis: GPF_HOST (padrão: daten), GPF_DIR (padrão: /srv/gpf)
set -euo pipefail

HOST="${GPF_HOST:-daten}"
DIR="${GPF_DIR:-/srv/gpf}"
OUT="models/gpf-risk.joblib"

if [[ $# -ge 1 ]]; then
  gpf-train --csv "$1" --out "$OUT"
else
  gpf-train --synthetic 400 --out "$OUT"
fi
SHA="$(cut -d' ' -f1 "$OUT.sha256")"

echo "→ Enviando modelo (${SHA:0:12}…) para ${HOST}:${DIR}/models/"
scp "$OUT" "$OUT.sha256" "${HOST}:${DIR}/models/"
# shellcheck disable=SC2029  # expansão local intencional
ssh "$HOST" "cd '$DIR' && chmod 0640 models/gpf-risk.joblib && sed -i 's/^GPF_MODEL_SHA256=.*/GPF_MODEL_SHA256=$SHA/' .env \
  && docker compose --env-file .env up -d --force-recreate api"
echo "✓ Modelo publicado. Teste: curl https://${HOST}.<sua-tailnet>.ts.net/health"
