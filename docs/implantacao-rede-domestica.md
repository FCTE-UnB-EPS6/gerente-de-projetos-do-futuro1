# Implantação em rede privada doméstica (DATEN + Mac Mini)

Guia para colocar o GPF em produção em casa, sem expor nada à internet.
Decisão registrada no [ADR 0003](adr/0003-implantacao-rede-privada-domestica.md).

## 1. Topologia

```
                 Internet (nenhuma porta aberta no roteador)
                              │
                   ┌──────────┴──────────┐
                   │  Tailnet (WireGuard)│  ← só seus dispositivos
                   └───┬─────────────┬───┘
                       │             │
   ┌───────────────────┴──┐     ┌────┴───────────────────────────┐
   │ Mac Mini (macOS)     │     │ DATEN (Linux, SSD 1 TB) 24/7   │
   │ • desenvolvimento    │ ssh │ • Docker: gpf-api (127.0.0.1)  │
   │ • treino (gpf-train) ├────►│ • tailscale serve → HTTPS      │
   │ • publicar-modelo.sh │ scp │ • n8n + PostgreSQL (já existem)│
   └──────────────────────┘     │ • /srv/gpf (modelos, .env)     │
                                └────────────────────────────────┘
   Celular/notebook na tailnet → https://daten.<tailnet>.ts.net
```

| Máquina | Papel | Por quê |
|---|---|---|
| **DATEN** | Produção 24/7 | Linux, SSD de 1 TB, já roda n8n e PostgreSQL endurecidos. Imagem `amd64` publicada pela esteira. |
| **Mac Mini** | Desenvolvimento e treino | Apple Silicon treina os modelos rápido; mantém o servidor livre de ferramentas de build. |

## 2. Rede privada com Tailscale

1. Instale o Tailscale no DATEN (`curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`), no Mac Mini (App Store) e no celular.
2. No painel do Tailscale, ative **MagicDNS** e **HTTPS Certificates**.
3. No roteador: **desative UPnP** e confirme que não há *port forwarding* para o DATEN.
4. (Recomendado) ACL da tailnet permitindo apenas seus dispositivos nas portas 22 e 443 do DATEN.

## 3. Endurecimento do DATEN

```bash
# SSH: só chave, sem root, só pela tailnet
sudo tee /etc/ssh/sshd_config.d/10-gpf.conf >/dev/null <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AllowUsers SEU_USUARIO
EOF
sudo systemctl reload ssh

# Firewall: nega tudo que entra; libera SSH apenas na interface da tailnet
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on tailscale0 to any port 22 proto tcp
sudo ufw allow in on tailscale0 to any port 443 proto tcp   # tailscale serve (HTTPS do GPF)
sudo ufw enable

# Atualizações de segurança automáticas
sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades
```

No Mac Mini, crie a chave e um apelido de SSH:

```bash
ssh-keygen -t ed25519 -C "mac-mini→daten"
ssh-copy-id SEU_USUARIO@daten
# ~/.ssh/config
# Host daten
#   HostName daten          # nome MagicDNS
#   User SEU_USUARIO
```

> Lembre: quem está no grupo `docker` tem poder de root. Mantenha só o seu usuário nele.

## 4. Primeira implantação no DATEN

```bash
# Estrutura no SSD
sudo groupadd -g 10001 gpf                 # mesmo GID do container
sudo usermod -aG gpf "$USER"               # saia e entre de novo na sessão
sudo mkdir -p /srv/gpf/models
sudo chown -R "$USER":gpf /srv/gpf
chmod 2750 /srv/gpf/models                 # setgid: arquivos novos herdam o grupo gpf

# Arquivos de implantação (do repositório)
cd /srv/gpf
REPO=https://raw.githubusercontent.com/FCTE-UnB-EPS6/gerente-de-projetos-do-futuro1/main/deploy
curl -fsSLO "$REPO/docker-compose.yml"
curl -fsSLO "$REPO/atualizar.sh" && chmod +x atualizar.sh
curl -fsSL "$REPO/.env.example" -o .env && chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # cole em GPF_API_TOKEN no .env
```

**Imagem.** A esteira de entrega publica `ghcr.io/fcte-unb-eps6/gerente-de-projetos-do-futuro1` a cada merge na `main`.
Se o pacote estiver privado no GHCR, faça login com um *token* de leitura (escopo `read:packages`):
`echo "$TOKEN" | docker login ghcr.io -u SEU_USUARIO_GITHUB --password-stdin`.
Alternativa sem registro: clone o repositório no DATEN e use a linha `build:` do `docker-compose.yml`.

## 5. Treinar e publicar o modelo (no Mac Mini)

```bash
git clone https://github.com/FCTE-UnB-EPS6/gerente-de-projetos-do-futuro1 && cd gerente-de-projetos-do-futuro1
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[ml]"            # acrescente ,xgboost para usar o XGBoost
deploy/publicar-modelo.sh         # base sintética; para dados reais: deploy/publicar-modelo.sh dados/historico.csv
```

O script treina, grava o `.joblib` com o `.sha256`, envia ao DATEN por `scp`, fixa `GPF_MODEL_SHA256` no `.env` e reinicia a API.
**A API recusa qualquer modelo cujo hash não confira**, porque o formato joblib executa código ao ser carregado.

Formato do CSV real: colunas `technical_complexity` (1–10), `scope_changes`, `team_turnover_pct`, `spi`, `cpi`,
`technical_debt_hours`, `overrun` (0/1), `budget_deviation_pct` e, opcional, `risk_narrative`. Mínimo de 20 projetos encerrados.

## 6. Subir a API e publicar na tailnet

```bash
cd /srv/gpf
docker compose --env-file .env up -d
curl -fsS http://127.0.0.1:8000/health
sudo tailscale serve --bg 8000              # HTTPS válido em https://daten.<tailnet>.ts.net
```

Teste de qualquer dispositivo da tailnet:

```bash
curl -s https://daten.<tailnet>.ts.net/ml/predict \
  -H "Authorization: Bearer $GPF_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"project_name":"PRJ-01","technical_complexity":9,"scope_changes":7,"team_turnover_pct":22,
       "spi":0.84,"cpi":0.88,"technical_debt_hours":140,
       "risk_narrative":"Atraso na homologação de segurança no pipeline CI/CD"}'
```

A documentação interativa fica em `https://daten.<tailnet>.ts.net/docs`.

> Nunca use `tailscale funnel`: ele publica na internet aberta.

## 7. Atualizações

```bash
/srv/gpf/atualizar.sh <sha-do-commit>   # prefira o SHA a "latest": reprodutível e auditável
```

O script baixa a imagem, sobe, testa `/health` por até 60 s e **volta à versão anterior** se falhar.

## 8. Integração com o n8n (já no DATEN)

Fluxo sugerido: *Schedule* semanal → lê as métricas dos projetos (planilha, PostgreSQL ou API do GitHub)
→ *HTTP Request* `POST http://127.0.0.1:8000/ml/predict` com o token → envia as propostas ao Discord para aprovação.
Se o n8n roda em container, `127.0.0.1` aponta para o próprio container: conecte-o à rede do GPF
(`docker network connect gpf_default <container-do-n8n>`) e use `http://api:8000/ml/predict`. As propostas chegam com status `pendente`: a decisão continua humana.

## 9. Backup (regra 3-2-1)

O que importa: `/srv/gpf/.env`, `/srv/gpf/models/` e, quando houver persistência, o banco do GPF no PostgreSQL.

```bash
# Exemplo com restic para um disco externo ou para o Mac Mini via SFTP
restic -r sftp:mac-mini:/Volumes/Backup/gpf init
restic -r sftp:mac-mini:/Volumes/Backup/gpf backup /srv/gpf
```

Agende no cron e **teste a restauração** pelo menos uma vez por semestre.

## 10. Checklist de go-live

- [ ] Nenhuma porta encaminhada no roteador; UPnP desligado
- [ ] SSH só com chave e só pela `tailscale0`; `ufw status` sem regras abertas para a LAN
- [ ] `.env` com `chmod 600` e `GPF_API_TOKEN` definido
- [ ] `GPF_MODEL_SHA256` preenchido; `/ml/predict` responde 200 com token e 401 sem
- [ ] `GPF_IMAGE_TAG` fixado num SHA
- [ ] Backup agendado e uma restauração testada

## 11. O que NÃO fazer

- **Não registre o DATEN nem o Mac Mini como *runner* auto-hospedado do GitHub Actions.** O repositório é público:
  um PR de terceiros pode executar código na sua rede doméstica. A esteira continua na nuvem do GitHub; o DATEN só *puxa* a imagem.
- Não treine modelos com dados reais de alunos ou de projetos sem anonimizar antes (LGPD).
- Não monte o diretório de modelos com escrita no container.
