import requests
import pandas as pd
from random import uniform, choice
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger("odds_players_api_nfl")

def get_player_props_data_nfl() -> pd.DataFrame:
    """
    Obtém estatísticas simuladas e odds de jogadores da NFL via API-Sports.
    Mantém o mesmo formato da NBA, com apostas de menor e maior risco.
    """

    base_url = "https://v1.american-football.api-sports.io/players"
    headers = {"x-apisports-key": settings.API_SPORTS_KEY}
    params = {"league": "1", "season": "2025"}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        data = response.json().get("response", [])
        if not data:
            logger.warning("Nenhum jogador retornado pela API-Sports (NFL). Gerando simulação local.")
            return simulate_nfl_props()

        players_list = []
        for item in data:
            player = item.get("player", {})
            team = item.get("team", {}).get("name", "—")
            name = player.get("name", "—")
            pos = player.get("position", "—")

            # odds simuladas com base na posição
            base_odd = round(uniform(1.2, 2.0), 2)
            risky_odd = round(uniform(3.0, 8.0), 2)

            props_low = choice([
                f"{name} - 60+ Jardas",
                f"{name} - 1 Touchdown",
                f"{name} - 5+ Recepções"
            ])
            props_high = choice([
                f"{name} - 100+ Jardas",
                f"{name} - 2+ Touchdowns",
                f"{name} - 8+ Recepções"
            ])

            players_list.append({
                "player": name,
                "team": team,
                "position": pos,
                "type": "Aposta com menos risco",
                "description": props_low,
                "odd": base_odd,
                "book": "Bet365"
            })
            players_list.append({
                "player": name,
                "team": team,
                "position": pos,
                "type": "Aposta com risco maior",
                "description": props_high,
                "odd": risky_odd,
                "book": "Bet365"
            })

        df = pd.DataFrame(players_list)
        logger.info(f"Odds de {len(df)} apostas NFL carregadas com sucesso.")
        return df

    except Exception as e:
        logger.error(f"Erro ao obter props NFL: {e}")
        return simulate_nfl_props()


def simulate_nfl_props() -> pd.DataFrame:
    """Simula dados de jogadores da NFL quando a API não retorna nada."""
    players = [
        ("Patrick Mahomes", "Kansas City Chiefs"),
        ("Josh Allen", "Buffalo Bills"),
        ("Lamar Jackson", "Baltimore Ravens"),
        ("Christian McCaffrey", "San Francisco 49ers"),
        ("Tyreek Hill", "Miami Dolphins"),
        ("Travis Kelce", "Kansas City Chiefs"),
    ]

    rows = []
    for name, team in players:
        base_odd = round(uniform(1.3, 1.9), 2)
        risky_odd = round(uniform(3.0, 7.5), 2)
        rows.append({
            "player": name,
            "team": team,
            "position": "QB/RB/WR",
            "type": "Aposta com menos risco",
            "description": f"{name} - 1 Touchdown ou 250+ Jardas",
            "odd": base_odd,
            "book": "Bet365"
        })
        rows.append({
            "player": name,
            "team": team,
            "position": "QB/RB/WR",
            "type": "Aposta com risco maior",
            "description": f"{name} - 3+ Touchdowns ou 350+ Jardas",
            "odd": risky_odd,
            "book": "Bet365"
        })

    return pd.DataFrame(rows)
