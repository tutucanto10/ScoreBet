import requests
import pandas as pd
import logging

logger = logging.getLogger("[player_stats]")

# ✅ endpoint público, sem autenticação
BALLDONTLIE_URL = "https://api.balldontlie.io/nba/v1/stats"

def get_recent_player_stats(season=2024, per_page=100):
    """Obtém médias recentes dos jogadores da NBA (rota pública, sem key)"""
    try:
        players = []
        page = 1

        while True:
            params = {"season": season, "per_page": per_page, "page": page}
            r = requests.get(BALLDONTLIE_URL, params=params, timeout=15)
            if r.status_code == 401:
                logger.error("401 Unauthorized — rota incorreta para o plano gratuito.")
                break
            r.raise_for_status()

            data = r.json()
            if not data.get("data"):
                break

            for stat in data["data"]:
                players.append({
                    "player": f"{stat['player']['first_name']} {stat['player']['last_name']}",
                    "team": stat["team"]["full_name"],
                    "pts": stat.get("pts", 0),
                    "reb": stat.get("reb", 0),
                    "ast": stat.get("ast", 0),
                })

            page += 1
            if page > 5:  # evita excesso no plano free
                break

        df = pd.DataFrame(players)
        logger.info(f"{len(df)} estatísticas coletadas da BallDontLie (rota pública)")
        return df

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return pd.DataFrame()
