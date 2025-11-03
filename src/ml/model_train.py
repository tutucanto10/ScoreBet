# >>> INÍCIO: src/ml/model_train.py
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
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

from src.ml.features import build_feature_table

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True, parents=True)
MODEL_PATH = MODEL_DIR / "nba_baseline.pkl"

FEATURES = [
    "home_rpts","home_ropp","home_rwin",
    "away_rpts","away_ropp","away_rwin",
    "diff_rpts","diff_ropp","diff_rwin",
]

def train_baseline(last_n: int = 5) -> dict:
    df = build_feature_table(last_n=last_n)
    if df.empty:
        return {"ok": False, "msg": "Sem dados suficientes para treinar."}

    X = df[FEATURES].values.astype(float)
    y = df["home_win"].values.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=200, n_jobs=None)
    model.fit(X_train, y_train)

    p_train = model.predict_proba(X_train)[:,1]
    p_test  = model.predict_proba(X_test)[:,1]

    acc = accuracy_score(y_test, (p_test >= 0.5).astype(int))
    auc = roc_auc_score(y_test, p_test)

    joblib.dump({"model": model, "features": FEATURES, "last_n": last_n}, MODEL_PATH)

    return {
        "ok": True,
        "samples": len(df),
        "acc": float(acc),
        "auc": float(auc),
        "model_path": str(MODEL_PATH),
    }
# >>> FIM
