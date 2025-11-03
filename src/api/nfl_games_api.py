import requests
import pandas as pd
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("nfl_games_api")

def get_nfl_games_data() -> pd.DataFrame:
    """
    Obtém os jogos da NFL (temporada atual) via API-Sports.
    Retorna DataFrame com times, data, horário, semana e local.
    """
    base_url = "https://v1.american-football.api-sports.io/games"
    headers = {"x-apisports-key": settings.API_SPORTS_KEY}
    params = {"league": "1", "season": "2025"}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json().get("response", [])
        if not data:
            logger.warning("Nenhum jogo retornado pela API-Sports.")
            return pd.DataFrame()

        games = []
        for g in data:
            fixture = g.get("game", {})
            teams = g.get("teams", {})
            venue = g.get("venue", {})

            games.append({
                "id": fixture.get("id"),
                "date": fixture.get("date"),
                "time": fixture.get("time", "TBD"),
                "week": fixture.get("week", "—"),
                "home_team": teams.get("home", {}).get("name", "—"),
                "away_team": teams.get("away", {}).get("name", "—"),
                "venue": venue.get("name", "—")
            })

        return pd.DataFrame(games)

    except Exception as e:
        logger.error(f"Erro ao buscar jogos da NFL: {e}")
        return pd.DataFrame()
