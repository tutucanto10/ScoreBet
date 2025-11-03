# >>> INÍCIO: src/ml/upcoming.py
from __future__ import annotations
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import joblib
import pandas as pd
import numpy as np
from sqlalchemy import select
from datetime import date, timedelta
from src.db.setup import SessionLocal
from src.db.models import NBAGame
from src.ml.model_train import FEATURES, MODEL_DIR
from src.api.nba_data import get_upcoming_games


# ======================================================
# ESTATÍSTICAS RECENTES (com pesos e split casa/fora)
# ======================================================
def _team_recent_stats(df_hist: pd.DataFrame, last_n: int = 5) -> pd.DataFrame:
    """Retorna um DF com uma linha por time e stats ponderadas recentes (até hoje)."""
    home = df_hist[["date","home_team","home_score","visitor_score"]].copy()
    home.columns = ["date","team","pts","opp"]
    away = df_hist[["date","visitor_team","visitor_score","home_score"]].copy()
    away.columns = ["date","team","pts","opp"]

    long = pd.concat([home, away], ignore_index=True).sort_values(["team","date"])
    long["win"] = (long["pts"] > long["opp"]).astype(int)
    long["days_ago"] = (pd.to_datetime(date.today()) - long["date"]).dt.days

    rec = long[long["date"] < pd.to_datetime(date.today())].groupby("team").tail(last_n)
    # pesos: jogos mais recentes têm mais influência
    rec["weight"] = np.exp(-0.15 * rec["days_ago"].clip(0, 10))

    agg = rec.groupby("team").apply(
        lambda g: pd.Series({
            "rpts": np.average(g["pts"], weights=g["weight"]),
            "ropp": np.average(g["opp"], weights=g["weight"]),
            "rwin": np.average(g["win"], weights=g["weight"]),
        })
    ).reset_index()

    return agg


# ======================================================
# MONTA FEATURES PARA PRÓXIMOS JOGOS
# ======================================================
def make_upcoming_features(days_ahead: int = 3, last_n: int = 5) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = s.execute(select(NBAGame)).scalars().all()
    if not rows:
        return pd.DataFrame()

    df_hist = pd.DataFrame([{
        "date": pd.to_datetime(r.date),
        "home_team": r.home_team,
        "visitor_team": r.visitor_team,
        "home_score": r.home_score,
        "visitor_score": r.visitor_score,
    } for r in rows]).sort_values("date")

    stats = _team_recent_stats(df_hist, last_n=last_n)

    df_up = get_upcoming_games(days_ahead=days_ahead)
    if df_up.empty:
        return pd.DataFrame()

    feat_rows = []
    for _, g in df_up.iterrows():
        h, a = g["home_team"], g["visitor_team"]
        sh, sa = stats[stats["team"] == h], stats[stats["team"] == a]
        if sh.empty or sa.empty:
            continue

        row = {
            "date": pd.to_datetime(g["date"]),
            "season": g["season"],
            "home_team": h,
            "visitor_team": a,
            "home_rpts": sh["rpts"].values[0],
            "home_ropp": sh["ropp"].values[0],
            "home_rwin": sh["rwin"].values[0],
            "away_rpts": sa["rpts"].values[0],
            "away_ropp": sa["ropp"].values[0],
            "away_rwin": sa["rwin"].values[0],
        }

        # features diferenciais
        row["diff_rpts"] = row["home_rpts"] - row["away_rpts"]
        row["diff_ropp"] = row["home_ropp"] - row["away_ropp"]
        row["diff_rwin"] = row["home_rwin"] - row["away_rwin"]
        row["power_index"] = (
            0.6 * row["diff_rpts"] - 0.4 * row["diff_ropp"] + 0.8 * row["diff_rwin"]
        )
        feat_rows.append(row)

    return pd.DataFrame(feat_rows)


# ======================================================
# PREDIÇÃO FINAL
# ======================================================
def predict_upcoming(days_ahead: int = 3, last_n: int = 5) -> pd.DataFrame:
    """Retorna DF com jogos futuros + p_home_win (usando modelo salvo ou heurística)."""
    df_feat = make_upcoming_features(days_ahead=days_ahead, last_n=last_n)
    if df_feat.empty:
        return df_feat

    try:
        bundle = joblib.load(MODEL_DIR / "nba_baseline.pkl")
        model, cols = bundle["model"], bundle["features"]
        df_feat = df_feat.dropna(subset=cols)
        proba = model.predict_proba(df_feat[cols].values)[:, 1]
    except Exception:
        # fallback heurístico leve se modelo não existir
        proba = 1 / (1 + np.exp(-df_feat["power_index"].fillna(0)))

    df_feat["p_home_win"] = proba
    df_feat["p_away_win"] = 1 - proba
    df_feat["pick_side"] = np.where(
        df_feat["p_home_win"] >= 0.55, "Mandante",
        np.where(df_feat["p_away_win"] >= 0.55, "Visitante", "Nenhum")
    )
    df_feat["conf"] = (df_feat["p_home_win"] - 0.5).abs() * 200

    return df_feat.sort_values("date").reset_index(drop=True)
# >>> FIM
