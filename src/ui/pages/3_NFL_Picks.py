import streamlit as st
import pandas as pd
from src.api.nfl_picks_api import get_nfl_picks_data  # novo módulo

st.set_page_config(page_title="NFL Picks", layout="wide")
st.title("🏈 NFL: Picks para Hoje")

df = get_nfl_picks_data()

if df is None or df.empty:
    st.warning("Nenhum pick disponível para hoje na NFL.")
    st.stop()

grouped = df.groupby("game")
for game, group in grouped:
    st.markdown(f"## 🏆 {game}")
    st.table(group[["pick", "odd", "book", "risk_level"]])
