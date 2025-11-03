# >>> INÍCIO: src/ml/predict.py
from __future__ import annotations
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

MODEL_PATH = Path("models") / "nba_baseline.pkl"

def predict_proba_home(df_features: pd.DataFrame) -> np.ndarray:
    """Recebe DataFrame com as mesmas colunas de treino e devolve P(home_win)."""
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    cols  = bundle["features"]
    X = df_features[cols].values.astype(float)
    return model.predict_proba(X)[:,1]
# >>> FIM
