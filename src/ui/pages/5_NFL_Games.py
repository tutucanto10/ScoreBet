import streamlit as st
import pandas as pd
from src.api.nfl_games_api import get_nfl_games_data

st.set_page_config(page_title="NFL Games", layout="wide")

st.title("🏈 NFL: Jogos por Semana")

# Carrega os jogos
df = get_nfl_games_data()

if df is None or df.empty:
    st.warning("Nenhum jogo disponível no momento.")
    st.stop()

# Converter datas
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["week"] = df["week"].astype(str)

# Filtro de semanas disponíveis
weeks = sorted(df["week"].unique())
selected_week = st.selectbox("📆 Escolha a semana:", weeks, index=len(weeks)-1)

# Filtrar os jogos da semana selecionada
week_games = df[df["week"] == selected_week]

if week_games.empty:
    st.warning(f"Nenhum jogo encontrado para a semana {selected_week}.")
    st.stop()

# Agrupar por dia
days = sorted(week_games["date"].dt.date.unique())

for day in days:
    st.markdown(f"### 📅 {day.strftime('%d/%m/%Y')}")
    day_games = week_games[week_games["date"].dt.date == day]

    for _, row in day_games.iterrows():
        home, away = row["home_team"], row["away_team"]
        time = row.get("time", "Horário indefinido")
        venue = row.get("venue", "Local não informado")
        st.markdown(f"""
        <div style='background-color:#111;padding:15px;border-radius:10px;margin-bottom:10px;'>
            <b>{away} 🆚 {home}</b><br>
            🕐 <b>{time}</b><br>
            📍 {venue}
        </div>
        """, unsafe_allow_html=True)
