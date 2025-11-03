import requests
import pandas as pd
import logging

logger = logging.getLogger("[odds_players]")

# 🔑 Chave correta da TheOddsAPI (https://the-odds-api.com)
ODDS_API_KEY = "2bffbe055e722a54e9cb3c27454c4665"

# ✅ Endpoint atualizado 2025
BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

def get_bet365_player_props(markets=None):
    """Obtém as linhas de player props da Bet365 (via TheOddsAPI)"""
    if markets is None:
        markets = ["player_points", "player_rebounds", "player_assists"]

    all_data = []

    for market in markets:
        params = {
            "regions": "us,br",
            "oddsFormat": "decimal",
            "markets": market,
            "bookmakers": "bet365",
            "apiKey": ODDS_API_KEY,
        }

        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            if r.status_code == 401:
                logger.error("401 Unauthorized — verifique sua API key da TheOddsAPI.")
                return pd.DataFrame()
            r.raise_for_status()

            games = r.json()

            for g in games:
                bookmaker = next((b for b in g.get("bookmakers", []) if b["key"] == "bet365"), None)
                if not bookmaker:
                    continue

                for market_data in bookmaker.get("markets", []):
                    for outcome in market_data.get("outcomes", []):
                        all_data.append({
                            "home_team": g["home_team"],
                            "away_team": g["away_team"],
                            "market": market_data["key"],
                            "player": outcome["name"],
                            "price": outcome.get("price"),
                            "point_line": outcome.get("point", None)
                        })
        except Exception as e:
            logger.error(f"[{market}] erro: {e}")

    df = pd.DataFrame(all_data)
    logger.info(f"Retornadas {len(df)} linhas de player props")
    return df
