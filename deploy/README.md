# Implantação no servidor da universidade

Este guia é para quem administra o servidor (TI). A instalação é feita uma vez e leva cerca de 20 minutos. Depois disso, nenhuma ação manual é necessária para atualizar o sistema.

## Como funciona

```
merge na main ──► CI verde ──► imagem :<sha> no GHCR
                                   │
                                   ├─► tag :homologacao  (automático)
                                   └─► tag :producao     (só com aprovação no GitHub)

servidor (a cada 2 min) ──► docker compose pull ──► atualiza o que mudou
```

- O servidor **busca** as imagens no GHCR (saída HTTPS para `ghcr.io`). O GitHub **nunca** acessa o servidor: não é preciso abrir porta no firewall, criar usuário SSH nem guardar chave no GitHub.
- Homologação e produção rodam no mesmo servidor, em containers separados, presos ao `localhost`.
- O acesso externo passa pelo proxy reverso (HTTPS) que a TI já usa.

| Ambiente | Container | Porta local | Tag da imagem | Quem promove |
| --- | --- | --- | --- | --- |
| Homologação | `gpf-homologacao` | `127.0.0.1:8001` | `homologacao` | Automático, a cada merge |
| Produção | `gpf-producao` | `127.0.0.1:8000` | `producao` | Aprovação manual no GitHub |

## Requisitos do servidor

- Linux com systemd (Ubuntu 22.04+ ou Debian 12+)
- Docker Engine 24+ com o plugin `docker compose`
- Saída HTTPS liberada para `ghcr.io` e `pkg-containers.githubusercontent.com`
- 1 vCPU e 1 GB de RAM livres (cada ambiente usa no máximo 512 MB)

## Instalação

```bash
# 1. Usuário de serviço sem login
sudo useradd --system --create-home --shell /usr/sbin/nologin gpf
sudo usermod -aG docker gpf

# 2. Arquivos de implantação
sudo mkdir -p /opt/gpf/.docker
cd /tmp && git clone --depth 1 https://github.com/FCTE-UnB-EPS6/gerente-de-projetos-do-futuro1.git
sudo cp gerente-de-projetos-do-futuro1/deploy/docker-compose.yml gerente-de-projetos-do-futuro1/deploy/atualizar.sh /opt/gpf/
sudo chmod 750 /opt/gpf/atualizar.sh
sudo chown -R gpf:gpf /opt/gpf

# 3. Atualização automática a cada 2 minutos
sudo cp gerente-de-projetos-do-futuro1/deploy/systemd/gpf-atualizar.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gpf-atualizar.timer

# 4. Primeira execução e conferência
sudo systemctl start gpf-atualizar.service
journalctl -u gpf-atualizar.service -n 20
curl -s http://127.0.0.1:8001/health   # homologação
curl -s http://127.0.0.1:8000/health   # produção (depois da primeira aprovação)
```

> Atenção: quem está no grupo `docker` tem, na prática, poder de root na máquina. O usuário `gpf` não tem login nem senha, e o serviço roda com `NoNewPrivileges` e sistema de arquivos protegido.

## Proxy reverso (HTTPS)

Publique os dois ambientes por nomes separados, com certificado válido. Exemplo para nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name gpf.exemplo.unb.br;            # produção
    # ssl_certificate / ssl_certificate_key conforme o padrão da TI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
# Repita com server_name gpf-homolog.exemplo.unb.br e proxy_pass http://127.0.0.1:8001
```

Recomenda-se restringir a homologação à rede da universidade ou à VPN.

## Operação

| Tarefa | Como fazer |
| --- | --- |
| Ver o que está rodando | `docker ps --filter name=gpf-` |
| Ver a versão de cada ambiente | `docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.revision" }}' gpf-producao` |
| Ver o histórico de atualizações | `journalctl -u gpf-atualizar.service --since today` |
| Logs da aplicação | `docker logs --tail 100 gpf-producao` |
| Forçar atualização agora | `sudo systemctl start gpf-atualizar.service` |
| Voltar para uma versão anterior | No GitHub: Actions → **Promover versão (rollback)** → informar o SHA e o ambiente. O servidor aplica em até 2 minutos |
| Pausar atualizações | `sudo systemctl stop gpf-atualizar.timer` |

## Segurança dos containers

Cada container roda sem root, com sistema de arquivos somente leitura, sem capacidades do kernel (`cap_drop: ALL`), sem escalonamento de privilégio, com limite de memória, CPU e processos, e com rotação de logs. A imagem é verificada pelo Trivy antes de ser publicada.
