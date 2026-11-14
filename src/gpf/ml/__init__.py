"""Machine learning para gestão de riscos (extra opcional `ml`).

Camada de infraestrutura: depende de scikit-learn/numpy e implementa o protocolo
`gpf.agents.RiskModel`. O domínio continua puro.
"""

from gpf.ml.predictor import RiskPredictor, TrainingReport
from gpf.ml.store import load_model, save_model
from gpf.ml.synthetic import History, generate_history

__all__ = ["History", "RiskPredictor", "TrainingReport", "generate_history", "load_model", "save_model"]
