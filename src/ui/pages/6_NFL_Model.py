import streamlit as st
import pandas as pd
from src.api.nfl_model_api import get_nfl_model_predictions  # novo módulo

st.set_page_config(page_title="NFL Model", layout="wide")
st.title("🏈 NFL: Modelo de Previsões")

# Carrega previsões simuladas
df = get_nfl_model_predictions()

if df is None or df.empty:
    st.warning("Nenhuma previsão disponível para a NFL no momento.")
    st.stop()

st.dataframe(df)
