# >>> INÍCIO: src/api/odds_api.py

# --- PATH FIX: garante que "src" está acessível mesmo rodando direto ---
# --- PATH FIX GLOBAL (garante import de 'src' em qualquer execução) ---
import os, sys
HERE = os.path.abspath(os.path.dirname(__file__))        # .../src/api
SRC = os.path.abspath(os.path.join(HERE, ".."))          # .../src
ROOT = os.path.abspath(os.path.join(SRC, ".."))          # .../scorebet
for path in [SRC, ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from src.utils.config import settings
from src.utils.logger import get_logger

# -----------------------------------------------------------------------

import re
from datetime import datetime
import requests
import pandas as pd
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger("odds_api")

# ============================================================
# 🔧 Normalização de nomes
# ============================================================
def _norm_name(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = re.sub(r"\s+", " ", s)
    ALIAS = {
        "la clippers": "los angeles clippers",
        "la lakers": "los angeles lakers",
        "ny knicks": "new york knicks",
        "gs warriors": "golden state warriors",
        "okc thunder": "oklahoma city thunder",
        "gsw": "golden state warriors",
        "nyk": "new york knicks",
        "lal": "los angeles lakers",
        "lac": "los angeles clippers",
    }
    return ALIAS.get(s, s)

# ============================================================
# 🏀 TheOddsAPI — odds H2H
# ============================================================
def get_h2h_odds_theodds(book: str = "1xbet", days_to: int = 7) -> pd.DataFrame:
    """
    Busca odds H2H da The Odds API para NBA (hoje + próximos `days_to` dias).
    Retorna DataFrame com colunas:
    date, home_team, away_team, home_odds, away_odds, book
    """
    base_url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": settings.ODDS_API_KEY,
        "regions": "us,eu,uk",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "bookmakers": book,
        "dateFormat": "iso",
        "daysFrom": 0,
        "daysTo": max(0, int(days_to)),
    }

    try:
        r = requests.get(base_url, params=params, timeout=25)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"[theodds] erro HTTP/JSON: {e}")
        return pd.DataFrame()

    if not isinstance(data, list) or not data:
        logger.warning("[theodds] resposta vazia.")
        return pd.DataFrame()

    rows = []
    for ev in data:
        home = ev.get("home_team") or ev.get("teams", [None, None])[0] or ""
        away = ev.get("away_team") or ev.get("teams", [None, None])[1] or ""
        commence_iso = ev.get("commence_time", "")
        try:
            date = pd.to_datetime(commence_iso, utc=True)
        except Exception:
            date = None

        home_odd, away_odd = None, None
        for bm in ev.get("bookmakers", []):
            key = bm.get("key", "").lower()
            if book and key != book.lower():
                continue
            markets = bm.get("markets", [])
            target = next((m for m in markets if m.get("key") == "h2h"), None) or (markets[0] if markets else None)
            if not target:
                continue

            outcomes = target.get("outcomes", [])
            if not outcomes:
                continue

            home_key, away_key = _norm_name(home), _norm_name(away)
            for out in outcomes:
                nm = _norm_name(out.get("name", ""))
                price = out.get("price")
                if price is None:
                    continue
                if (home_odd is None) and (nm == home_key or home_key in nm or nm in home_key):
                    home_odd = price
                elif (away_odd is None) and (nm == away_key or away_key in nm or nm in away_key):
                    away_odd = price
            break  # só precisa do bookmaker principal

        rows.append({
            "date": date,
            "home_team": home,
            "away_team": away,
            "home_odds": home_odd,
            "away_odds": away_odd,
            "book": "Bet365" if book.lower() == "1xbet" else book.capitalize()
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("date", na_position="last").reset_index(drop=True)
    logger.info(f"[theodds] jogos retornados para {book}: {len(df)}")
    return df


# ============================================================
# Alias compatível para Player Picks (corrigido)
# ============================================================
def get_player_props_nba():
    """Obtém player props (pontos, assistências, rebotes) via TheOddsAPI com fallback público."""
    import requests
    import pandas as pd
    from src.utils.config import settings
    from src.utils.logger import get_logger

    logger = get_logger("odds_api")
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    markets = ["player_points", "player_assists", "player_rebounds"]
    regions = ["us"]

    all_rows = []

    # === 1️⃣ tenta a TheOddsAPI ===
    for market in markets:
        for region in regions:
            params = {
                "regions": region,
                "markets": market,
                "oddsFormat": "decimal",
                "apiKey": settings.ODDS_API_KEY,
            }
            try:
                r = requests.get(url, params=params, timeout=25)
                if r.status_code == 422:
                    logger.warning(f"[player_props] {market.upper()} não disponível na TheOddsAPI ({region})")
                    continue
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                logger.error(f"[player_props] erro {market.upper()} ({region}): {e}")
                continue

            for game in data:
                home = game.get("home_team")
                away = game.get("away_team")
                for bookmaker in game.get("bookmakers", []):
                    book = bookmaker.get("title")
                    for mkt in bookmaker.get("markets", []):
                        for outcome in mkt.get("outcomes", []):
                            all_rows.append({
                                "home_team": home,
                                "away_team": away,
                                "book": book,
                                "market": market,
                                "player": outcome.get("description"),
                                "line": outcome.get("point"),
                                "odd": outcome.get("price"),
                            })

    if len(all_rows) > 0:
        df = pd.DataFrame(all_rows)
        logger.info(f"[player_props] retornadas {len(df)} linhas de player props via TheOddsAPI.")
        return df

    # === 2️⃣ fallback público (BallDontLie API) ===
    try:
        logger.warning("[player_props] Fallback ativado — buscando dados no BallDontLie API...")
        resp = requests.get("https://www.balldontlie.io/api/v1/players?per_page=50", timeout=15)
        resp.raise_for_status()
        players = resp.json().get("data", [])
        df = pd.DataFrame([{
            "home_team": "Fallback",
            "away_team": "Fallback",
            "book": "BallDontLie",
            "market": "player_points",
            "player": f"{p['first_name']} {p['last_name']}",
            "line": None,
            "odd": None
        } for p in players])
        logger.info(f"[player_props] Fallback retornou {len(df)} jogadores fictícios para exibição temporária.")
        return df

    except Exception as e:
        logger.error(f"[player_props] fallback falhou: {e}")
        return pd.DataFrame()
# >>> FIM
