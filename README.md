# Gerente de Projetos do Futuro (GPF)

Aplicação de gerência de projetos **AI-First**, construída com **IA agêntica, Machine Learning e DevSecOps** desde o primeiro commit. Ela segue os referenciais **PMBOK® 8**, **PRINCE2® 7** e **PM4R** (Project Management for Results – BID).

> Disciplina EPS6 · FCTE / Universidade de Brasília

## Objetivo

Reduzir o esforço humano repetitivo da gerência de projetos com agentes de IA que:

- registram e acompanham o ciclo de vida do projeto (iniciação → encerramento);
- mantêm atualizados o registro de riscos, as questões e o *business case*;
- geram relatórios de progresso e alertas de desvio (prazo, custo, escopo);
- verificam a aderência às práticas dos três referenciais.

O humano decide; os agentes preparam, verificam e alertam.

## Stack

| Camada | Tecnologia |
|---|---|
| API | Python 3.12 + FastAPI |
| Domínio | Modelos puros em Python (sem dependência de framework) |
| ML de riscos | scikit-learn (gradient boosting, Random Forest, DBSCAN, TF-IDF); XGBoost e Transformers opcionais |
| Qualidade | Ruff (lint + format), Mypy, Pytest + cobertura |
| Segurança | CodeQL, Gitleaks, pip-audit, Dependabot, Trivy (imagem) |
| Entrega | Docker + GitHub Actions |
| Ambiente | Dev Container / GitHub Codespaces |

## Começando

### Opção 1 — Codespaces (recomendado)

No GitHub: **Code → Codespaces → Create codespace on main**. O ambiente sobe pronto, com dependências e hooks instalados.

### Opção 2 — Local

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
make test        # testes
make run         # API em http://localhost:8000 (docs em /docs)
```

### Risco preditivo (ML)

```bash
gpf-train --synthetic 400 --out models/gpf-risk.joblib   # ou --csv dados/historico.csv
export GPF_MODEL_PATH=models/gpf-risk.joblib GPF_MODEL_SHA256=<hash impresso pelo gpf-train>
make run   # POST /ml/predict devolve probabilidade de estouro, contingência, anomalia e propostas
```

### Opção 3 — Docker

```bash
docker build -t gpf .
docker run -p 8000:8000 gpf
```

## Estrutura

```
src/gpf/
  api/          # camada HTTP (FastAPI)
  domain/       # entidades e regras de GP (projeto, riscos, estágios)
  agents/       # agentes de IA (contratos e implementações)
  ml/           # modelos preditivos de risco e CLI gpf-train
deploy/         # produção na rede privada doméstica (docker compose, scripts)
tests/          # testes automatizados
docs/           # arquitetura, ADRs e mapeamento PMBOK/PRINCE2/PM4R
.github/        # CI/CD, segurança, templates e CODEOWNERS
.devcontainer/  # ambiente reprodutível (Codespaces)
```

## Fluxo de trabalho

1. Abra uma *issue* (template de funcionalidade ou bug).
2. Crie uma branch curta a partir de `main`: `feat/123-descricao`, `fix/…`, `docs/…`.
3. Faça commits no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/).
4. Abra um PR. A CI (lint, tipos, testes e segurança) precisa passar, e o CODEOWNER precisa aprovar.
5. *Squash merge* na `main`.

Mais detalhes em [CONTRIBUTING.md](CONTRIBUTING.md). Para vulnerabilidades, veja [SECURITY.md](SECURITY.md).

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [Mapeamento PMBOK 8 · PRINCE2 7 · PM4R](docs/referenciais.md)
- [Decisões de arquitetura (ADRs)](docs/adr/)
- [Implantação em rede privada doméstica (DATEN + Mac Mini)](docs/implantacao-rede-domestica.md)

## Licença

[MIT](LICENSE)
