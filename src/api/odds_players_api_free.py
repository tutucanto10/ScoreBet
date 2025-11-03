# ============================================================
# ScoreBet - Odds e Métricas Simuladas (Temporada 2025/2026)
# ============================================================

import requests
import random
import pandas as pd
import logging

# Configuração de logger
logger = logging.getLogger("[sportsdb_players_api_sim]")
logging.basicConfig(level=logging.INFO, format="%(message)s")

API_KEY = "123"  # plano gratuito
BASE_URL = "https://www.thesportsdb.com/api/v1/json"
TARGET_SEASON = "2025–2026"

# Times de exemplo
teams = [
    {"name": "Golden State Warriors", "id": "134867"},
    {"name": "Boston Celtics", "id": "134860"},
    {"name": "Los Angeles Lakers", "id": "134870"},
    {"name": "Dallas Mavericks", "id": "134869"},
    {"name": "Oklahoma City Thunder", "id": "134868"},
]

# ============================================================
# Funções
# ============================================================

def get_team_players(team_name: str, team_id: str):
    """Busca jogadores de um time e simula temporada 2025/2026"""
    try:
        url = f"{BASE_URL}/{API_KEY}/lookup_all_players.php"
        params = {"id": team_id}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("player", [])

        if not data:
            logger.warning(f"⚠️ Nenhum jogador encontrado para {team_name}")
            return []

        players = [
            {
                "name": f"{p.get('strPlayer', 'Desconhecido')}",
                "team": team_name,
                "thumb": p.get("strThumb") or "https://www.thesportsdb.com/images/media/player/thumb/blank.png",
                "points_avg": round(random.uniform(8, 28), 1),
                "rebounds_avg": round(random.uniform(3, 12), 1),
                "assists_avg": round(random.uniform(2, 9), 1),
            }
            for p in data if p.get("strSport") == "Basketball"
        ]

        logger.info(f"✅ {len(players)} jogadores simulados para {team_name} ({TARGET_SEASON})")
        return players

    except Exception as e:
        logger.error(f"Erro ao buscar jogadores de {team_name}: {e}")
        return []


def generate_odds(players):
    """Gera apostas simuladas (baixa e alta, compatíveis com layout do app)"""
    if not players:
        return pd.DataFrame()

    safe_bets = random.sample(players, min(3, len(players)))
    risky_bets = random.sample(players, min(3, len(players)))

    data = []

    # Apostas seguras (menos risco)
    for p in safe_bets:
        odd = round(random.uniform(1.4, 2.1), 2)
        pts_line = random.randint(10, 22)
        data.append({
            "team": p["team"],
            "player": p["name"],
            "type": "Aposta com menos risco",
            "stat": f"{pts_line}+ Pontos",
            "odd": odd,
            "thumb": p["thumb"],
            "market": random.choice(["player_points", "player_rebounds", "player_assists"]),
            "book": random.choice(["Betano", "Bet365", "Parimatch"]),
            "home_team": random.choice(["Lakers", "Warriors", "Celtics", "Mavericks", "Thunder"]),
            "away_team": random.choice(["Heat", "Bulls", "Nets", "Suns", "Kings"]),
            # 👇 coluna exigida pelo layout
            "line": f"+{pts_line}.5",
        })

    # Apostas de risco maior
    for p in risky_bets:
        odd = round(random.uniform(6.0, 10.0), 2)
        pts_line = random.randint(28, 40)
        data.append({
            "team": p["team"],
            "player": p["name"],
            "type": "Aposta com risco maior",
            "stat": f"{pts_line}+ Pontos",
            "odd": odd,
            "thumb": p["thumb"],
            "market": random.choice(["player_points", "player_rebounds", "player_assists"]),
            "book": random.choice(["Betano", "Bet365"]),
            "home_team": random.choice(["Lakers", "Warriors", "Celtics", "Mavericks", "Thunder"]),
            "away_team": random.choice(["Heat", "Bulls", "Nets", "Suns", "Kings"]),
            "line": f"+{pts_line}.5",
        })

    return pd.DataFrame(data)


def main():
    """Função principal (usada no terminal ou no app Streamlit)"""
    all_bets = []

    for t in teams:
        players = get_team_players(t["name"], t["id"])
        if players:
            odds_df = generate_odds(players)
            all_bets.append(odds_df)

    if not all_bets:
        logger.warning("⚠️ Nenhum dado coletado.")
        return pd.DataFrame()

    df = pd.concat(all_bets, ignore_index=True)
    return df


# ============================================================
# Integração com Streamlit
# ============================================================

def get_player_props_data():
    """Interface compatível com o Streamlit (Player Picks)"""
    try:
        df = main()
        if df.empty:
            logger.warning("⚠️ Nenhum dado disponível para Player Picks.")
            return pd.DataFrame()
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados simulados: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print(main())
