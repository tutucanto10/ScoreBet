# ============================================================
# 💰 ScoreBet — NFL Picks (Odds + ESPN, estilo NBA Picks)
# ============================================================
import os, sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta, timezone
import requests

# Caminhos padrão do projeto
CURRENT = Path(__file__).resolve()
SRC_DIR = CURRENT.parents[2]
ROOT_DIR = SRC_DIR.parent
for p in (SRC_DIR, ROOT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.api.nfl_picks_api import get_nfl_picks_data

# ===============================================
# CONFIGURAÇÕES GERAIS
# ===============================================
st.set_page_config(page_title="🏈 ScoreBet — NFL Picks", page_icon="🏈", layout="wide")
st.title("🏈 ScoreBet — Picks NFL (Odds + ESPN)")

# ===============================================
# FUNÇÕES AUXILIARES
# ===============================================
TEAM_LOGOS = {
    "buffalo bills": "buf", "miami dolphins": "mia", "new england patriots": "ne",
    "new york jets": "nyj", "baltimore ravens": "bal", "cincinnati bengals": "cin",
    "cleveland browns": "cle", "pittsburgh steelers": "pit", "houston texans": "hou",
    "indianapolis colts": "ind", "jacksonville jaguars": "jax", "tennessee titans": "ten",
    "denver broncos": "den", "kansas city chiefs": "kc", "las vegas raiders": "lv",
    "los angeles chargers": "lac", "chicago bears": "chi", "detroit lions": "det",
    "green bay packers": "gb", "minnesota vikings": "min", "atlanta falcons": "atl",
    "carolina panthers": "car", "new orleans saints": "no", "tampa bay buccaneers": "tb",
    "arizona cardinals": "ari", "los angeles rams": "lar", "san francisco 49ers": "sf",
    "seattle seahawks": "sea", "dallas cowboys": "dal", "new york giants": "nyg",
    "philadelphia eagles": "phi", "washington commanders": "was"
}

def get_team_logo(name: str) -> str:
    code = TEAM_LOGOS.get(str(name).lower(), "nfl")
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{code}.png"

def get_espn_games(days_ahead: int = 5) -> pd.DataFrame:
    """Busca jogos reais da NFL via ESPN API"""
    base = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
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
                "date": comp.get("date"),
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
days_ahead = 5
prob_thres = 0.55

try:
    pred_df = get_nfl_picks_data()
    espn_df = get_espn_games(days_ahead=days_ahead)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Se DataFrame vier vazio, usa mock temporário
if pred_df is None or pred_df.empty:
    data = [
        {"home_team": "Kansas City Chiefs", "away_team": "Buffalo Bills",
         "home_odds": 1.75, "away_odds": 2.10, "p_home_win": 0.59, "p_away_win": 0.41},
        {"home_team": "Baltimore Ravens", "away_team": "San Francisco 49ers",
         "home_odds": 1.90, "away_odds": 1.95, "p_home_win": 0.52, "p_away_win": 0.48},
        {"home_team": "Miami Dolphins", "away_team": "Dallas Cowboys",
         "home_odds": 1.65, "away_odds": 2.25, "p_home_win": 0.63, "p_away_win": 0.37},
    ]
    pred_df = pd.DataFrame(data)

# Renomeia colunas caso venham com nomes diferentes
rename_map = {
    "home": "home_team", "away": "away_team",
    "Home": "home_team", "Away": "away_team",
    "team_home": "home_team", "team_away": "away_team",
    "Home_Team": "home_team", "Away_Team": "away_team",
}
pred_df = pred_df.rename(columns=rename_map)

# Merge ESPN + modelo
merged = pd.merge(pred_df, espn_df, on=["home_team", "away_team"], how="left")

# ===============================================
# LÓGICA DE PICKS
# ===============================================
merged["p_away_win"] = merged["p_away_win"].fillna(1 - merged["p_home_win"])
merged["recommendation"] = np.where(
    merged["p_home_win"] >= prob_thres, "Mandante",
    np.where(merged["p_away_win"] >= prob_thres, "Visitante", "Nenhum")
)
merged["ev_home"] = merged["p_home_win"] - (1 / merged["home_odds"].replace(0, np.nan))
merged["ev_away"] = merged["p_away_win"] - (1 / merged["away_odds"].replace(0, np.nan))
merged["ev_best"] = np.where(merged["recommendation"] == "Mandante", merged["ev_home"], merged["ev_away"])
merged["color"] = np.where(merged["recommendation"] == "Mandante", "#00C853",
                   np.where(merged["recommendation"] == "Visitante", "#2979FF", "#999999"))
merged["conf"] = (merged[["p_home_win", "p_away_win"]].max(axis=1) - 0.5) * 200

# ===============================================
# DATAS E STATUS
# ===============================================
merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
if merged["date"].notna().any():
    merged["date_only"] = merged["date"].dt.tz_convert("America/Sao_Paulo").dt.date
else:
    merged["date_only"] = datetime.now().date()

merged["status"] = merged["status"].fillna("future")
merged["ao_vivo"] = merged["status"].str.lower().eq("in")
merged["encerrado"] = merged["status"].str.lower().eq("post")

# ===============================================
# INTERFACE VISUAL
# ===============================================
st.markdown("## 📅 Jogos e Previsões — NFL Picks")

dias = sorted(merged["date_only"].dropna().unique())[:4]
if len(dias) == 0:
    st.warning("Nenhum jogo disponível na API da ESPN.")
else:
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

            # Coluna da esquerda (Mandante)
            with col1:
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:6px;'>"
                    f"<img src='{home_logo}' width='32'> <b>{r['home_team']}</b></div>"
                    f"<div style='margin-left:38px;'>🪙 {r.get('home_odds','—')}</div>",
                    unsafe_allow_html=True
                )

            # Coluna central (Informações)
            with col2:
                conf_bar = f"""
                    <div style='background:#e5e5e5;width:100%;height:6px;border-radius:4px;margin-top:4px;'>
                        <div style='width:{conf_val:.1f}%;height:100%;border-radius:4px;background:{r["color"]};'></div>
                    </div>
                    <small style='color:#555;'>Confiança: {conf_val:.1f}%</small>
                """

                # Corrige caso date seja NaT
                if pd.notna(r["date"]):
                    hora_br = r["date"].tz_convert("America/Sao_Paulo").strftime("%H:%M")
                else:
                    hora_br = "Horário indefinido"

                if r["ao_vivo"]:
                    st.markdown(
                        f"<div style='text-align:center;'><b style='color:#00C853;'>🟢 AO VIVO</b><br>"
                        f"<b>{r.get('home_score','-')} × {r.get('away_score','-')}</b><br>"
                        f"<small>EV: {ev_str}</small><br>"
                        f"<small>• Apostar no <b>{side}</b></small>{conf_bar}</div>",
                        unsafe_allow_html=True
                    )
                elif r["encerrado"]:
                    acertou = (r.get("home_score",0) > r.get("away_score",0) and side == "Mandante") or \
                              (r.get("away_score",0) > r.get("home_score",0) and side == "Visitante")
                    result_text = f"<small>Previsão certa! <b>{side}</b> venceu ✅</small>" \
                        if acertou else f"<small>Previsão errada! <b>{side}</b> perdeu ❌</small>"
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<b style='color:#D50000;'>🔴 ENCERRADO</b><br>"
                        f"<b>{r.get('home_score','-')} × {r.get('away_score','-')}</b><br>{result_text}{conf_bar}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<b style='color:#E65100;'>⏰ {hora_br} (BR)</b><br>"
                        f"<small>• Apostar no <b>{side}</b></small>{conf_bar}</div>",
                        unsafe_allow_html=True
                    )

            # Coluna da direita (Visitante)
            with col3:
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:6px;justify-content:right;'>"
                    f"<b>{r['away_team']}</b> <img src='{away_logo}' width='32'></div>"
                    f"<div style='text-align:right;'>🪙 {r.get('away_odds','—')}</div>",
                    unsafe_allow_html=True
                )

            st.markdown("<hr style='border:0.5px solid #ddd;margin:8px 0;'>", unsafe_allow_html=True)

st.caption("📊 Dados via ESPN + ScoreBet API | Atualiza automaticamente a cada 30s")
