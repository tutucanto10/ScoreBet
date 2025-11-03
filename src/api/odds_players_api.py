import requests
import pandas as pd
from datetime import datetime, timezone
import logging

# Configuração do logger
logger = logging.getLogger(__name__)

# 🔑 Suas chaves (substitua pelas corretas)
THE_ODDS_API_KEY = "967e2bbc-fccf-4960-b0e1-13e2a135ed24"
SPORTSDATA_IO_KEY = "f97cc8a74a0f43a4b1ed0ff3fe7ea695"
BALLDONTLIE_KEY = "967e2bbc-fccf-4960-b0e1-13e2a135ed24"

# Endpoints
THE_ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
SPORTSDATA_URL = "https://api.sportsdata.io/v4/nba/stats/json/PlayerSeasonStatsBySeason/2025"
BALLDONTLIE_URL = "https://api.balldontlie.io/v1/stats"

# 🧠 Função principal híbrida
def get_player_props_data(days_ahead=3):
    """
    Coleta odds e métricas híbridas:
      1️⃣ Tenta pegar odds vivas (TheOddsAPI)
      2️⃣ Se falhar, usa médias históricas (SportsData.io)
      3️⃣ Se tudo falhar, fallback simples (BallDontLie)
    """
    all_rows = []

    # 1️⃣ --- TheOddsAPI (Bet365) ---
    try:
        params = {
            "apiKey": THE_ODDS_API_KEY,
            "regions": "us,uk,eu",
            "markets": "player_points",
            "oddsFormat": "decimal",
            "bookmakers": "bet365",
        }
        resp = requests.get(THE_ODDS_URL, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            for ev in data:
                home, away = ev.get("home_team"), ev.get("away_team")
                commence = ev.get("commence_time", "")[:16].replace("T", " ")

                for bm in ev.get("bookmakers", []):
                    if bm["key"] == "bet365":
                        for market in bm.get("markets", []):
                            for outcome in market.get("outcomes", []):
                                all_rows.append({
                                    "source": "TheOddsAPI",
                                    "matchup": f"{home} x {away}",
                                    "player": outcome.get("name"),
                                    "stat": market.get("key", "unknown"),
                                    "value": outcome.get("point", ""),
                                    "odd": outcome.get("price"),
                                    "type": "Baixo Risco" if outcome.get("price", 0) <= 2.10 else "Alto Risco",
                                    "date": commence
                                })
        else:
            logger.warning(f"TheOddsAPI retornou {resp.status_code}")

    except Exception as e:
        logger.error(f"Erro TheOddsAPI: {e}")

    # 2️⃣ --- SportsData.io ---
    if not all_rows:
        try:
            headers = {"Ocp-Apim-Subscription-Key": SPORTSDATA_IO_KEY}
            resp = requests.get(SPORTSDATA_URL, headers=headers, timeout=20)
            if resp.status_code == 200:
                players = resp.json()
                for p in players[:100]:  # limitar
                    player_name = p.get("Name")
                    pts = p.get("Points", 0)
                    reb = p.get("Rebounds", 0)
                    ast = p.get("Assists", 0)
                    avg = (pts + reb + ast) / 3 if any([pts, reb, ast]) else 0
                    all_rows.append({
                        "source": "SportsData.io",
                        "matchup": "—",
                        "player": player_name,
                        "stat": "Média Pts/Reb/Ast",
                        "value": round(avg, 1),
                        "odd": round(1.5 + avg / 10, 2),
                        "type": "Baixo Risco" if avg > 10 else "Alto Risco",
                        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                    })
            else:
                logger.warning(f"SportsData.io retornou {resp.status_code}")
        except Exception as e:
            logger.error(f"Erro SportsData.io: {e}")

    # 3️⃣ --- BallDontLie (fallback final) ---
    if not all_rows:
        try:
            headers = {"Authorization": BALLDONTLIE_KEY}
            params = {"per_page": 50}
            resp = requests.get(BALLDONTLIE_URL, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                stats = resp.json().get("data", [])
                for s in stats:
                    player = s["player"]["first_name"] + " " + s["player"]["last_name"]
                    pts = s.get("pts", 0)
                    reb = s.get("reb", 0)
                    ast = s.get("ast", 0)
                    avg = (pts + reb + ast) / 3
                    all_rows.append({
                        "source": "BallDontLie",
                        "matchup": s.get("game", {}).get("home_team", {}).get("full_name", "—") + " x " +
                                   s.get("game", {}).get("visitor_team", {}).get("full_name", "—"),
                        "player": player,
                        "stat": "Último jogo",
                        "value": round(avg, 1),
                        "odd": round(1.5 + avg / 10, 2),
                        "type": "Baixo Risco" if avg > 10 else "Alto Risco",
                        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                    })
            else:
                logger.warning(f"BallDontLie retornou {resp.status_code}")
        except Exception as e:
            logger.error(f"Erro BallDontLie: {e}")

    df = pd.DataFrame(all_rows)
    if df.empty:
        logger.warning("Nenhum dado retornado em nenhuma fonte.")
    else:
        logger.info(f"{len(df)} registros coletados de fontes híbridas.")

    return df


# 🔍 Teste local
if __name__ == "__main__":
    print("🔄 Testando coleta híbrida de métricas e odds...\n")
    df = get_player_props_data()
    if df.empty:
        print("⚠️ Nenhum dado retornado!")
    else:
        print(df.head(20))
