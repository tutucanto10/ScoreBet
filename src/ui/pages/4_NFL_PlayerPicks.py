import streamlit as st
import pandas as pd
from src.api.odds_players_api_nfl import get_player_props_data_nfl

st.set_page_config(page_title="NFL Player Picks", layout="wide")

st.markdown("""
    <style>
    .player-card {
        background-color: #111;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 15px;
        box-shadow: 0 0 10px rgba(0,0,0,0.4);
    }
    .player-img {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #00b4d8;
    }
    .player-info {
        color: #fff;
        font-size: 16px;
    }
    .section-title {
        color: #00b4d8;
        font-size: 22px;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏈 NFL Player Picks")
st.markdown("### As melhores apostas individuais da rodada")

# Carrega dados da API
df_players = get_player_props_data_nfl()

if df_players.empty:
    st.warning("Nenhum dado disponível no momento. Tente novamente mais tarde.")
    st.stop()

# Divide as apostas por tipo
df_low_risk = df_players[df_players["type"] == "Aposta com menos risco"]
df_high_risk = df_players[df_players["type"] == "Aposta com risco maior"]

# Função auxiliar para fotos
def get_player_image(player_name):
    name = player_name.lower().replace(" ", "-")
    return f"https://a.espncdn.com/i/headshots/nfl/players/full/{hash(name)%10000}.png"

# Sessão de apostas com menos risco
st.markdown('<div class="section-title">📉 Apostas com Menos Risco</div>', unsafe_allow_html=True)

for _, row in df_low_risk.head(6).iterrows():
    st.markdown(f"""
        <div class="player-card">
            <img src="{get_player_image(row['player'])}" class="player-img" onerror="this.src='https://cdn-icons-png.flaticon.com/512/21/21104.png'">
            <div class="player-info">
                <strong>{row['player']}</strong> ({row['team']})<br>
                <em>{row['description']}</em><br>
                💰 Odd: <b>{row['odd']}</b> — {row['book']}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Sessão de apostas com risco maior
st.markdown('<div class="section-title">🔥 Apostas com Risco Maior</div>', unsafe_allow_html=True)

for _, row in df_high_risk.head(6).iterrows():
    st.markdown(f"""
        <div class="player-card">
            <img src="{get_player_image(row['player'])}" class="player-img" onerror="this.src='https://cdn-icons-png.flaticon.com/512/21/21104.png'">
            <div class="player-info">
                <strong>{row['player']}</strong> ({row['team']})<br>
                <em>{row['description']}</em><br>
                💰 Odd: <b>{row['odd']}</b> — {row['book']}
            </div>
        </div>
    """, unsafe_allow_html=True)
