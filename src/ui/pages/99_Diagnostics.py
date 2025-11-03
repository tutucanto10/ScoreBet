# >>> INÍCIO: src/ui/pages/99_Diagnostics.py
from __future__ import annotations
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd

from src.api.nba_data import get_upcoming_games
from src.api.odds_api import get_h2h_odds_nba, get_player_props_nba

st.set_page_config(page_title="Diagnostics", page_icon="🛠️", layout="wide")
st.title("🛠️ Diagnostics – NBA")

with st.sidebar:
    st.header("Parâmetros")
    days = st.slider("Dias à frente (balldontlie/props)", 1, 7, 3, 1)
    st.caption("Use este painel para verificar se há dados das APIs, livros disponíveis e casamento por jogo.")

# 1) balldontlie – próximos jogos
up = get_upcoming_games(days_ahead=days)
st.subheader("Próximos jogos (balldontlie)")
st.write(f"Total de jogos (próximos {days}d): {0 if up is None else len(up)}")
st.dataframe(up.head(20) if up is not None else pd.DataFrame(), use_container_width=True)

# 2) OddsAPI – H2H
odds = get_h2h_odds_nba()
st.subheader("Odds H2H (OddsAPI)")
if odds is None or odds.empty:
    st.warning("OddsAPI não retornou H2H agora.")
else:
    st.write("Livros disponíveis:", sorted(odds['book'].dropna().unique().tolist()))
    st.dataframe(odds.head(50), use_container_width=True)

# 3) Casamento por jogo (seletor)
if up is not None and not up.empty and odds is not None and not odds.empty:
    st.subheader("Casamento por jogo (nome normalizado)")
    games = up[['home_team','visitor_team']].astype(str).drop_duplicates().apply(lambda r: f"{r['home_team']} x {r['visitor_team']}", axis=1).tolist()
    choice = st.selectbox("Escolha um confronto:", games)
    home, away = choice.split(" x ", 1)
    # tentar match por nomes 'crus'
    sub = odds[(odds['home_team'].astype(str).str.strip()==home) & (odds['away_team'].astype(str).str.strip()==away)]
    st.write("Linhas por casas (match por nomes crus):", len(sub))
    st.dataframe(sub, use_container_width=True)

# 4) Player Props (por evento)
st.subheader("Player Props (OddsAPI por evento)")
props = get_player_props_nba(days_ahead=days)
if props is None or props.empty:
    st.info("Sem props retornadas agora (pode ser limitação do plano/horário).")
else:
    st.write("Livros (props):", sorted(props['book'].dropna().unique().tolist()))
    st.dataframe(props.head(50), use_container_width=True)
# >>> FIM
