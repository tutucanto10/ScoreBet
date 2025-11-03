import requests
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_h2h_odds_1xbet() -> pd.DataFrame:
    """
    Busca odds da NBA diretamente da 1xBet Brasil.
    Retorna DataFrame com home_team, away_team, odds e data.
    """
    url = (
        "https://1xbet.bet.br/LineFeed/Get1x2_VZip"
        "?sports=3&count=100&lng=pt-BR&tf=2200000&mode=4"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://1xbet.bet.br/line/basketball/",
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        events = data.get("Value", [])
        if not events:
            logger.warning("Nenhum evento encontrado na 1xBet.")
            return pd.DataFrame()

        rows = []
        for ev in events:
            league = ev.get("L", "")
            if "NBA" not in league.upper():
                continue  # filtra apenas NBA

            home = ev.get("O1", "").strip()
            away = ev.get("O2", "").strip()

            ev_data = ev.get("E", [])
            if not ev_data or len(ev_data) < 2:
                continue

            home_odds = ev_data[0].get("C")
            away_odds = ev_data[1].get("C")

            ts = ev.get("S")
            date = (
                datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                if ts
                else None
            )

            if home and away:
                rows.append({
                    "date": date,
                    "home_team": home,
                    "away_team": away,
                    "home_odds": home_odds,
                    "away_odds": away_odds,
                    "book": "Bet365"
                })

        df = pd.DataFrame(rows)
        df = df.sort_values("date", ascending=True).reset_index(drop=True)

        logger.info(f"Odds NBA carregadas da 1xBet: {len(df)} jogos.")
        return df

    except Exception as e:
        logger.error(f"Erro ao obter odds da 1xBet: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    df = get_h2h_odds_1xbet()
    print(df.head())
    print(f"\nTotal de jogos carregados: {len(df)}")
