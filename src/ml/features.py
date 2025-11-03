# >>> INÍCIO: src/ml/features.py
from __future__ import annotations
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pandas as pd
from sqlalchemy import select
from datetime import datetime
from src.db.setup import SessionLocal
from src.db.models import NBAGame

def _team_roll_stats(games: pd.DataFrame, last_n: int = 5) -> pd.DataFrame:
    """
    Gera estatísticas por time ao longo do tempo (rolling, antes do jogo).
    Retorna DF com colunas para home_* e visitor_* + label home_win.
    """
    df = games.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # transforma em linhas por time (lado "team", "pts", "opp", "is_home")
    home = df[["date","home_team","home_score","visitor_score"]].copy()
    home.columns = ["date","team","pts","opp"]
    home["is_home"] = 1
    away = df[["date","visitor_team","visitor_score","home_score"]].copy()
    away.columns = ["date","team","pts","opp"]
    away["is_home"] = 0
    long = pd.concat([home, away], ignore_index=True)
    long["win"] = (long["pts"] > long["opp"]).astype(int)

    # rolling por time, EXCLUINDO o próprio jogo (shift)
    long = long.sort_values(["team","date"])
    for col in ["pts","opp","win"]:
        long[f"r{last_n}_{col}"] = (
            long.groupby("team")[col]
                .apply(lambda s: s.shift().rolling(last_n, min_periods=1).mean())
                .values
        )

    # agora voltamos ao formato por partida juntando stats do time da casa e do visitante
    # mapeia stats por (team,date) para merge rápido
    key = ["team","date"]
    stats_cols = [f"r{last_n}_pts", f"r{last_n}_opp", f"r{last_n}_win"]
    stats = long[key + stats_cols]

    # junta no dataframe de jogos
    m_home = df.merge(stats, left_on=["home_team","date"], right_on=["team","date"], how="left")
    m_home = m_home.rename(columns={
        f"r{last_n}_pts": "home_rpts",
        f"r{last_n}_opp": "home_ropp",
        f"r{last_n}_win": "home_rwin",
    }).drop(columns=["team"])

    m_both = m_home.merge(stats, left_on=["visitor_team","date"], right_on=["team","date"], how="left")
    m_both = m_both.rename(columns={
        f"r{last_n}_pts": "away_rpts",
        f"r{last_n}_opp": "away_ropp",
        f"r{last_n}_win": "away_rwin",
    }).drop(columns=["team"])

    # label
    m_both["home_win"] = (m_both["home_score"] > m_both["visitor_score"]).astype(int)

    # features básicas + controle de home advantage
    feat = m_both[[
        "game_id","date","season","home_team","visitor_team",
        "home_rpts","home_ropp","home_rwin",
        "away_rpts","away_ropp","away_rwin",
        "home_win"
    ]].copy()

    # algumas derivadas simples
    feat["diff_rpts"] = feat["home_rpts"] - feat["away_rpts"]
    feat["diff_ropp"] = feat["home_ropp"] - feat["away_ropp"]
    feat["diff_rwin"] = feat["home_rwin"] - feat["away_rwin"]

    # drop qualquer linha muito antiga sem histórico
    feat = feat.dropna().reset_index(drop=True)
    return feat

def build_feature_table(last_n: int = 5) -> pd.DataFrame:
    """Lê jogos do banco e monta tabela de features/label."""
    with SessionLocal() as s:
        rows = s.execute(select(NBAGame)).scalars().all()
    if not rows:
        return pd.DataFrame()

    games = pd.DataFrame([{
        "game_id": r.game_id,
        "date": r.date,
        "season": r.season,
        "home_team": r.home_team,
        "visitor_team": r.visitor_team,
        "home_score": r.home_score,
        "visitor_score": r.visitor_score,
    } for r in rows])

    return _team_roll_stats(games, last_n=last_n)
# >>> FIM
