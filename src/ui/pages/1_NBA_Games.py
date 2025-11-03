import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone
from dateutil import parser
import time
import os

# ===============================================
# CONFIG
# ===============================================
st.set_page_config(page_title="🏀 ScoreBet — Jogos NBA", page_icon="🏀", layout="wide")
st.title("🏀 ScoreBet — Jogos da NBA (Datas, Horários e Transmissão)")

# ===============================================
# FUNÇÕES AUXILIARES
# ===============================================
TEAM_LOGOS = {
    "atlanta hawks": "atl", "boston celtics": "bos", "brooklyn nets": "bkn", "charlotte hornets": "cha",
    "chicago bulls": "chi", "cleveland cavaliers": "cle", "dallas mavericks": "dal", "denver nuggets": "den",
    "detroit pistons": "det", "golden state warriors": "gs", "houston rockets": "hou", "indiana pacers": "ind",
    "la clippers": "lac", "los angeles lakers": "lal", "memphis grizzlies": "mem", "miami heat": "mia",
    "milwaukee bucks": "mil", "minnesota timberwolves": "min", "new orleans pelicans": "no", "new york knicks": "ny",
    "oklahoma city thunder": "okc", "orlando magic": "orl", "philadelphia 76ers": "phi", "phoenix suns": "phx",
    "portland trail blazers": "por", "sacramento kings": "sac", "san antonio spurs": "sa", "toronto raptors": "tor",
    "utah jazz": "utah", "washington wizards": "was"
}

def get_team_logo(name: str) -> str:
    """Retorna o logo oficial da equipe."""
    code = TEAM_LOGOS.get(str(name).lower(), "nba")
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{code}.png"

def to_brazil_time(utc_str):
    try:
        if not utc_str:
            return None
        dt_utc = parser.isoparse(utc_str)
        return dt_utc.astimezone(timezone(timedelta(hours=-3)))
    except Exception:
        return None

# ===============================================
# ESPN + TheOddsAPI
# ===============================================
def fetch_from_espn():
    """Busca jogos da ESPN (ao vivo, horários e canais)"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        games = []
        for ev in data.get("events", []):
            comp = ev.get("competitions", [{}])[0]
            status_type = comp.get("status", {}).get("type", {})
            state = status_type.get("state", "").lower()  # in, post, pre
            status_detail = status_type.get("description", "")
            comps = comp.get("competitors", [])

            home = next((c for c in comps if c.get("homeAway") == "home"), {})
            away = next((c for c in comps if c.get("homeAway") == "away"), {})

            home_team = home.get("team", {}).get("displayName", "—")
            away_team = away.get("team", {}).get("displayName", "—")
            home_score = home.get("score")
            away_score = away.get("score")

            br_dt = to_brazil_time(comp.get("date"))
            canais = ", ".join([b.get("names", [])[0] for b in comp.get("broadcasts", [])]) or "NBA League Pass"

            games.append({
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "hora_br": br_dt.strftime("%H:%M") if br_dt else "—",
                "broadcast": canais,
                "ao_vivo": state == "in",
                "encerrado": state == "post",
                "status_detail": status_detail,
                "date_only": br_dt.date() if br_dt else datetime.now().date(),
                "start_time": br_dt
            })
        return pd.DataFrame(games)
    except Exception:
        return pd.DataFrame()

def fetch_from_oddsapi():
    """Busca jogos futuros via TheOddsAPI"""
    api_key = os.getenv("ODDS_API_KEY", "YOUR_API_KEY_HERE")
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=h2h"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        games = []
        for g in data:
            if not g.get("commence_time"):
                continue
            br_dt = to_brazil_time(g["commence_time"])
            games.append({
                "home_team": g.get("home_team"),
                "away_team": g.get("away_team"),
                "home_score": None,
                "away_score": None,
                "hora_br": br_dt.strftime("%H:%M") if br_dt else "—",
                "broadcast": "NBA League Pass",
                "ao_vivo": False,
                "encerrado": False,
                "status_detail": "Agendado",
                "date_only": br_dt.date() if br_dt else datetime.now().date(),
                "start_time": br_dt
            })
        return pd.DataFrame(games)
    except Exception:
        return pd.DataFrame()

# ===============================================
# INTERFACE
# ===============================================
placeholder = st.empty()
refresh_interval = 30

while True:
    with placeholder.container():
        espn_df = fetch_from_espn()
        odds_df = fetch_from_oddsapi()

        df = pd.concat([espn_df, odds_df], ignore_index=True)
        df = df.drop_duplicates(subset=["home_team", "away_team"], keep="first")

        # remove jogos encerrados há mais de 1 dia
        now = datetime.now(timezone(timedelta(hours=-3)))
        df = df[~((df["encerrado"]) & ((now - df["start_time"]) > timedelta(hours=6)))]

        if df.empty:
            st.warning("Nenhum jogo ativo ou futuro encontrado — ESPN e TheOddsAPI sem dados disponíveis.")
            st.stop()

        st.markdown("## 📅 Jogos por Dia — NBA Schedule")

        # agrupar e mostrar os próximos 3 dias
        dias = sorted(df["date_only"].unique())[:3]
        for day in dias:
            date_label = pd.to_datetime(day).strftime("%d/%m (%A)")
            st.markdown(f"### 🗓️ {date_label}")

            day_games = df[df["date_only"] == day]
            for _, r in day_games.iterrows():
                col1, col2, col3 = st.columns([3, 1.5, 3])
                home_logo = get_team_logo(r["home_team"])
                away_logo = get_team_logo(r["away_team"])

                with col1:
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:6px;'>"
                        f"<img src='{home_logo}' width='28'> <b>{r['home_team']}</b></div>",
                        unsafe_allow_html=True
                    )

                with col2:
                    if r["ao_vivo"]:
                        st.markdown(
                            f"<div style='text-align:center;'>"
                            f"<b style='color:#00C853;'>🟢 AO VIVO</b><br>"
                            f"<b>{r['home_score']} × {r['away_score']}</b><br>"
                            f"<small>📺 {r['broadcast']}</small></div>",
                            unsafe_allow_html=True
                        )
                    elif r["encerrado"]:
                        st.markdown(
                            f"<div style='text-align:center;'>"
                            f"<b style='color:#D50000;'>🔴 ENCERRADO</b><br>"
                            f"<b>{r['home_score']} × {r['away_score']}</b><br>"
                            f"<small>📅 Começou em {r['date_only'].strftime('%d/%m')}</small></div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='text-align:center;'>"
                            f"<b style='color:#E65100;'>VS</b><br>"
                            f"<b style='color:#E65100;'>{r['hora_br']} (BR)</b><br>"
                            f"<small>📺 {r['broadcast']}</small></div>",
                            unsafe_allow_html=True
                        )

                with col3:
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:6px;justify-content:right;'>"
                        f"<b>{r['away_team']}</b> <img src='{away_logo}' width='28'></div>",
                        unsafe_allow_html=True
                    )

                st.markdown("<hr style='border:0.5px solid #ddd;margin:8px 0;'>", unsafe_allow_html=True)

        st.caption(f"🔄 Atualiza automaticamente a cada {refresh_interval}s")
    time.sleep(refresh_interval)
