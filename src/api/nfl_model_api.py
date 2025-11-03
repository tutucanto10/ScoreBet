import pandas as pd
from random import random

def get_nfl_model_predictions() -> pd.DataFrame:
    """Simula previsões de vitórias para jogos da NFL."""
    teams = [
        ("Cowboys", "Eagles"), ("Bills", "Dolphins"),
        ("Chiefs", "Broncos"), ("49ers", "Seahawks")
    ]
    data = []
    for home, away in teams:
        p_home = round(random(), 2)
        data.append({
            "home_team": home,
            "away_team": away,
            "p_home_win": p_home,
            "p_away_win": round(1 - p_home, 2)
        })
    return pd.DataFrame(data)
