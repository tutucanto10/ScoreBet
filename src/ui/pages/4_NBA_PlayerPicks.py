# ============================================================
# 🏀 Player Picks — Layout Final (corrigido, só jogadores ativos)
# ============================================================
import streamlit as st
import pandas as pd
import requests
from src.api.odds_players_api_free import get_player_props_data

st.set_page_config(page_title="Player Picks", layout="wide")
st.title("🏀 Sugestões de Player Picks")

# ============================================================
# Carrega dados simulados
# ============================================================
df = get_player_props_data()

if df is None or df.empty:
    st.warning("Nenhum dado de player props disponível no momento (as casas podem não ter aberto ainda).")
    st.stop()

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
            # Ignora técnicos, ex-jogadores e perfis sem imagem
            if (
                player.get("strPosition") not in ["Head Coach", "Manager", None]
                and player.get("strThumb")
            ):
                return player["strThumb"]
    except Exception:
        pass
    # fallback genérico
    return "https://cdn-icons-png.flaticon.com/512/616/616408.png"

# ============================================================
# Agrupar por jogo e exibir picks
# ============================================================
grouped_games = df.groupby(["home_team", "away_team"])
st.markdown("### 🎯 Picks do Dia (Simulados)")

for (home, away), game in grouped_games:
    st.markdown(f"## 🏆 {home} x {away}")

    col1, col2 = st.columns(2)

    # -----------------------------
    # 🟢 Apostas com menos risco
    # -----------------------------
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
                        <span style='font-size:14px;color:#444;'>{r["stat"]}</span><br>
                        <b style='color:#2c7;'>Odd:</b> {r["odd"]} — <i>{r["book"]}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # -----------------------------
    # 🔴 Apostas com risco maior
    # -----------------------------
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
                        <span style='font-size:14px;color:#444;'>{r["stat"]}</span><br>
                        <b style='color:#c00;'>Odd:</b> {r["odd"]} — <i>{r["book"]}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

st.caption("📊 Dados simulados via SportsDB + ScoreBet API | Retratos reais via TheSportsDB.com")
