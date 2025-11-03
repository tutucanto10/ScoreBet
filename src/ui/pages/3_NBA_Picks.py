# ============================================================
# 💰 ScoreBet — NBA Picks (Atualizado com ESPN e barra de confiança)
# ============================================================
import os, sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, timezone
import requests

# 🔧 Corrige import do src
CURRENT = Path(__file__).resolve()
SRC_DIR = CURRENT.parents[2]
ROOT_DIR = SRC_DIR.parent
for p in (SRC_DIR, ROOT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.ml.upcoming import predict_upcoming
from src.api.odds_api import get_h2h_odds_theodds

# ===============================================
# CONFIG
# ===============================================
st.set_page_config(page_title="💰 ScoreBet — NBA Picks", page_icon="💰", layout="wide")
st.title("💰 ScoreBet — Picks NBA (Bet365)")

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
def get_team_logo(name):
    code = TEAM_LOGOS.get(str(name).lower(), "nba")
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{code}.png"

def get_espn_games(days_ahead=3):
    """Busca jogos reais da ESPN (com status real e placares)."""
    base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    all_games = []
    today = datetime.now(timezone(timedelta(hours=-3)))
    for i in range(days_ahead):
        date = (today + timedelta(days=i)).strftime("%Y%m%d")
        resp = requests.get(f"{base}?dates={date}")
        if resp.status_code != 200:
            continue
        for ev in resp.json().get("events", []):
            comp = ev.get("competitions", [])[0]
            home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
            away = next(c for c in comp["competitors"] if c["homeAway"] == "away")
            all_games.append({
                "date": comp["date"],
                "home_team": home["team"]["displayName"],
                "away_team": away["team"]["displayName"],
                "status": comp["status"]["type"]["name"],
                "home_score": home.get("score"),
                "away_score": away.get("score"),
            })
    return pd.DataFrame(all_games)

# ===============================================
# DADOS
# ===============================================
days_ahead = 3
last_n = 5
prob_thres = 0.55

try:
    pred_df = predict_upcoming(days_ahead=days_ahead, last_n=last_n)
    odds_df = get_h2h_odds_theodds(book="pinnacle", days_to=days_ahead)
    espn_df = get_espn_games(days_ahead=days_ahead)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

rename_map = {"team_home": "home_team", "team_away": "away_team", "visitor_team": "away_team"}
pred_df = pred_df.rename(columns=rename_map)
odds_df = odds_df.rename(columns=rename_map)

# Merge
merged = pd.merge(pred_df, odds_df, on=["home_team", "away_team"], how="left")
merged = pd.merge(merged, espn_df, on=["home_team", "away_team"], how="left", suffixes=("", "_espn"))

# ===============================================
# LÓGICA DE PICKS
# ===============================================
merged["p_away_win"] = 1 - merged["p_home_win"]
merged["recommendation"] = np.where(
    merged["p_home_win"] >= prob_thres, "Mandante",
    np.where(merged["p_away_win"] >= prob_thres, "Visitante", "Nenhum")
)
merged["ev_home"] = merged["p_home_win"] - (1 / merged["home_odds"].replace(0, np.nan))
merged["ev_away"] = merged["p_away_win"] - (1 / merged["away_odds"].replace(0, np.nan))
merged["ev_best"] = np.where(merged["recommendation"] == "Mandante", merged["ev_home"], merged["ev_away"])
merged["color"] = np.where(merged["recommendation"] == "Mandante", "#00C853",
                   np.where(merged["recommendation"] == "Visitante", "#2979FF", "#999999"))
merged["conf"] = (merged["p_home_win"] - 0.5).abs() * 200

# ===============================================
# STATUS REAL (usando ESPN)
# ===============================================
merged["date"] = pd.to_datetime(merged["date"])
now = datetime.now(timezone.utc)
merged["ao_vivo"] = merged["status"].str.lower().eq("in")
merged["encerrado"] = merged["status"].str.lower().eq("post")
merged["futuro"] = merged["status"].str.lower().eq("status_future")
merged["date_only"] = merged["date"].dt.tz_convert("America/Sao_Paulo").dt.date

# ===============================================
# INTERFACE VISUAL
# ===============================================
st.markdown("## 📅 Jogos por Dia — NBA Picks (ao vivo + confiança)")

dias = sorted(merged["date_only"].dropna().unique())[:3]
for dia in dias:
    st.markdown(f"### 🗓️ {pd.to_datetime(dia).strftime('%d/%m (%A)')}")
    day_games = merged[merged["date_only"] == dia]

    for _, r in day_games.iterrows():
        col1, col2, col3 = st.columns([3, 1.5, 3])
        home_logo = get_team_logo(r["home_team"])
        away_logo = get_team_logo(r["away_team"])

        ev_str = f"{r['ev_best']*100:.1f}%" if pd.notna(r['ev_best']) else "—"
        side = r["recommendation"]
        conf_val = min(max(r.get("conf", 0), 0), 100)

        with col1:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:6px;'>"
                f"<img src='{home_logo}' width='28'> <b>{r['home_team']}</b></div>"
                f"<div style='margin-left:33px;'>🪙 {r.get('home_odds','—')}</div>",
                unsafe_allow_html=True
            )

        with col2:
            conf_bar = f"""
                <div style='background:#e5e5e5;width:100%;height:6px;border-radius:4px;margin-top:4px;'>
                    <div style='width:{conf_val:.1f}%;height:100%;border-radius:4px;background:{r["color"]};'></div>
                </div>
                <small style='color:#555;'>Confiança: {conf_val:.1f}%</small>
            """

            if r["ao_vivo"]:
                st.markdown(
                    f"<div style='text-align:center;'><b style='color:#00C853;'>🟢 AO VIVO</b><br>"
                    f"<b>{r['home_score']} × {r['away_score']}</b><br>"
                    f"<small>EV: {ev_str}</small><br>"
                    f"<small>• Apostar no <b>{side}</b></small>{conf_bar}</div>",
                    unsafe_allow_html=True
                )
            elif r["encerrado"]:
                acertou = (r["home_score"] > r["away_score"] and side == "Mandante") or \
                          (r["away_score"] > r["home_score"] and side == "Visitante")
                result_text = f"<small>Previsão certa! <b>{side}</b> venceu ✅</small>" \
                    if acertou else f"<small>Previsão errada! <b>{side}</b> perdeu ❌</small>"
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<b style='color:#D50000;'>🔴 ENCERRADO</b><br>"
                    f"<b>{r['home_score']} × {r['away_score']}</b><br>{result_text}{conf_bar}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<b style='color:#E65100;'>⏰ {r['date'].tz_convert('America/Sao_Paulo').strftime('%H:%M')} (BR)</b><br>"
                    f"<small>• Apostar no <b>{side}</b></small>{conf_bar}</div>",
                    unsafe_allow_html=True
                )

        with col3:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:6px;justify-content:right;'>"
                f"<b>{r['away_team']}</b> <img src='{away_logo}' width='28'></div>"
                f"<div style='text-align:right;'>🪙 {r.get('away_odds','—')}</div>",
                unsafe_allow_html=True
            )

        st.markdown("<hr style='border:0.5px solid #ddd;margin:8px 0;'>", unsafe_allow_html=True)

st.caption("🔄 Atualiza automaticamente a cada 30s")
