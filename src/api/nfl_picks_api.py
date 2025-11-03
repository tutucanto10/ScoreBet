import requests
import pandas as pd
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("nfl_picks_api")

def get_nfl_picks_data() -> pd.DataFrame:
    """Obtém odds de jogos da NFL via API-Sports"""
    base_url = "https://v1.odds.api-sports.io/odds"
    headers = {"x-apisports-key": settings.API_SPORTS_KEY}
    params = {
        "sport": "american-football",
        "region": "us",
        "league": "1",
        "season": "2025"
    }

    try:
        r = requests.get(base_url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("response", [])
        rows = []
        for g in data:
            game = g["fixture"]["teams"]
            for b in g.get("bookmakers", []):
                for m in b.get("bets", []):
                    if m["name"].lower() == "winner":
                        for o in m["values"]:
                            rows.append({
                                "game": f"{game['home']['name']} x {game['away']['name']}",
                                "pick": o["value"],
                                "odd": o["odd"],
                                "book": b["name"]
                            })
        df = pd.DataFrame(rows)
        logger.info(f"{len(df)} odds NFL carregadas com sucesso.")
        return df
    except Exception as e:
        logger.error(f"Erro ao coletar odds NFL: {e}")
        return pd.DataFrame()
