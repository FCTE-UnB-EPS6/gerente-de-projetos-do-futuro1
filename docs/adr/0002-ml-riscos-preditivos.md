# ADR 0002 — Machine learning para gestão preditiva de riscos

- **Status:** proposto
- **Data:** 2026-11-14

## Contexto

A matriz probabilidade × impacto do `RiskRegister` é subjetiva. O material de referência
"20 algoritmos fundamentais de ML aplicados à gestão de riscos" propõe usar dados históricos
para prever estouro de prazo/custo, calibrar a contingência, detectar projetos atípicos e
minerar texto das matrizes de risco.

## Decisão

1. Criar a camada `gpf.ml` (extra opcional `ml`), fora do domínio:
   - **Gradient boosting** para a probabilidade de estouro crítico. Motor padrão:
     `HistGradientBoostingClassifier` (scikit-learn); **XGBoost** quando o extra `xgboost` estiver instalado.
   - **Random Forest** para o desvio de orçamento esperado, que vira a sugestão de reserva de contingência.
   - **DBSCAN** para anomalias; um projeto novo é atípico se fica a mais de `eps` de toda amostra-núcleo.
   - **Índice semântico** da narrativa de risco: TF-IDF de n-gramas de caracteres (padrão, leve) ou
     Sentence-Transformers multilíngue (extra `nlp`).
   - **Explicabilidade** por importância de permutação, exibida como os três principais fatores.
2. O domínio ganha apenas objetos de valor puros: `ProjectMetrics`, `RiskPrediction` e `RiskDriver`.
3. O `PredictiveRiskAgent` depende do protocolo `RiskModel`, não do scikit-learn, e só gera
   `AgentProposal` pendentes (*human-in-the-loop*).
4. O modelo é gravado com joblib e **verificado por SHA-256 antes da desserialização**; a produção
   só carrega o hash fixado em `GPF_MODEL_SHA256`.
5. Enquanto não houver base real, o treino usa dados sintéticos com a regra latente do material de referência.

## Consequências

- Imagem Docker cresce (~150 MB) com scikit-learn; `EXTRAS=none` gera a imagem mínima.
- O XGBoost e os Transformers ficam opcionais para não pesar no servidor doméstico.
- Métricas de treino (ROC-AUC, MAE) vão no relatório do `gpf-train`; o próximo passo é rodá-las na CI
  como *evals* com limiar mínimo.
- Fica para depois: regressão logística calibrada para *score* de farol, RNN/séries temporais de SPI/CPI,
  PCA para índice de saúde e mineração de contratos com Transformers.
