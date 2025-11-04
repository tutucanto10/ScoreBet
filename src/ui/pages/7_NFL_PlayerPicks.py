# ============================================================
# 🏈 NFL Player Picks — Layout igual ao NBA Player Picks (corrigido e estável)
# ============================================================
import streamlit as st
import pandas as pd
import requests
from src.api.odds_players_api_nfl import get_player_props_data_nfl

st.set_page_config(page_title="NFL Player Picks", layout="wide")
st.title("🏈 NFL Player Picks")

# ============================================================
# Dados simulados (mock)
# ============================================================
df = get_player_props_data_nfl()

if df is None or df.empty:
    st.warning("Nenhum dado de player props disponível no momento (dados simulados).")
    st.stop()

# ============================================================
# Garante colunas de jogo (mock se não existirem)
# ============================================================
if "home_team" not in df.columns or "away_team" not in df.columns:
    # Remove valores nulos e cria lista única de times
    teams = df["team"].dropna().unique().tolist()

    # Se número de times for ímpar, ignora o último
    if len(teams) % 2 != 0:
        teams = teams[:-1]

    # Cria pares de times (jogos simulados)
    fake_games = []
    for i in range(0, len(teams), 2):
        fake_games.append((teams[i], teams[i + 1]))

    # Cria dicionário de mapeamento: cada time aponta pro seu jogo
    mapping = {}
    for home, away in fake_games:
        mapping[home] = (home, away)
        mapping[away] = (home, away)

    # Preenche colunas de jogo com fallback
    df["home_team"] = df["team"].apply(lambda t: mapping.get(t, ("Time A", "Time B"))[0] if pd.notna(t) else "Time A")
    df["away_team"] = df["team"].apply(lambda t: mapping.get(t, ("Time A", "Time B"))[1] if pd.notna(t) else "Time B")

# ============================================================
# Função para buscar retrato real do jogador
# ============================================================
@st.cache_data(show_spinner=False)
def get_player_image(player_name):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={player_name.replace(' ', '_')}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data and data.get("player"):
            player = data["player"][0]
            if player.get("strThumb"):
                return player["strThumb"]
    except Exception:
        pass
    return "https://cdn-icons-png.flaticon.com/512/21/21104.png"

# ============================================================
# Agrupar por jogo e exibir picks
# ============================================================
grouped_games = df.groupby(["home_team", "away_team"])
st.markdown("### 🎯 Picks da Rodada (Simulados)")

for (home, away), game in grouped_games:
    st.markdown(f"## 🏆 {home} x {away}")

    col1, col2 = st.columns(2)

    # 🟢 Apostas com menos risco
    with col1:
        st.subheader("🟢 Aposta com menos risco")
        safe_picks = game[game["type"] == "Aposta com menos risco"].head(3)
        if safe_picks.empty:
            st.info("Sem apostas seguras disponíveis neste jogo.")
        else:
            for _, r in safe_picks.iterrows():
                player_img = get_player_image(r["player"])
                st.markdown(f"""
                <div style='display:flex;align-items:center;background:#f8fff8;border:1px solid #c8f0c8;
                            border-radius:12px;padding:10px;margin-bottom:10px;'>
                    <img src='{player_img}' width='70' style='border-radius:10px;margin-right:12px;'>
                    <div>
                        <b style='font-size:16px;'>{r["player"]}</b><br>
                        <span style='font-size:14px;color:#444;'>{r["description"]}</span><br>
                        <b style='color:#2c7;'>Odd:</b> {r["odd"]} — <i>{r["book"]}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 🔴 Apostas com risco maior
    with col2:
        st.subheader("🔴 Aposta com risco maior")
        risky_picks = game[game["type"] == "Aposta com risco maior"].head(3)
        if risky_picks.empty:
            st.info("Sem apostas arriscadas disponíveis neste jogo.")
        else:
            for _, r in risky_picks.iterrows():
                player_img = get_player_image(r["player"])
                st.markdown(f"""
                <div style='display:flex;align-items:center;background:#fff8f8;border:1px solid #f0c8c8;
                            border-radius:12px;padding:10px;margin-bottom:10px;'>
                    <img src='{player_img}' width='70' style='border-radius:10px;margin-right:12px;'>
                    <div>
                        <b style='font-size:16px;'>{r["player"]}</b><br>
                        <span style='font-size:14px;color:#444;'>{r["description"]}</span><br>
                        <b style='color:#c00;'>Odd:</b> {r["odd"]} — <i>{r["book"]}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

st.caption("📊 Dados simulados via ScoreBet API | Retratos reais via TheSportsDB.com")
