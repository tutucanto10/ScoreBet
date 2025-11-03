# === FIX de caminho para Streamlit/Windows ===
import sys, pathlib
SRC_DIR = pathlib.Path(__file__).resolve().parents[1]  # .../scorebet/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# Agora importamos a partir de 'ml' diretamente
from ml.pipeline import train_baseline_classifier
# =============================================

# src/ui/app.py
import streamlit as st

st.set_page_config(
    page_title="ScoreBet",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",  # força sidebar aberta
)

st.title("🎯 ScoreBet — Protótipo")
st.write("Use o menu **Pages** (barra lateral) para navegar. Ex.: **NBA — Jogos Recentes**.")
import pandas as pd
import numpy as np
import plotly.express as px


st.set_page_config(page_title="ScoreBet — Protótipo", layout="wide")

st.title("🏀🏈⚽ ScoreBet — Protótipo (MVP)")
st.markdown("""
Protótipo inicial para validar **UI + pipeline** com dados fictícios.
Próximo passo: rotinas de **coleta NBA / Futebol / NFL** e banco de dados.
""")

# ----- dados mock (removeremos quando ligar as APIs) -----
np.random.seed(42)
n = 300
df = pd.DataFrame({
    "elo_home": np.random.normal(1550, 60, n),
    "elo_away": np.random.normal(1520, 60, n),
    "form_home": np.random.uniform(0, 1, n),
    "form_away": np.random.uniform(0, 1, n),
    "pace_or_possession": np.random.normal(100, 10, n),
})
df["home_win"] = (
    (df["elo_home"] - df["elo_away"])
    + (df["form_home"] - df["form_away"]) * 50
    + np.random.normal(0, 20, n)
) > 10
df["home_win"] = df["home_win"].astype(int)

st.subheader("Dados fictícios (amostra)")
st.dataframe(df.head(10), use_container_width=True)

with st.spinner("Treinando baseline..."):
    model, metrics = train_baseline_classifier(df.copy(), target_col="home_win")

st.success(f"Acurácia: **{metrics['accuracy']:.3f}** | ROC AUC: **{metrics['roc_auc']:.3f}**")

# Probabilidade predita vs diferença de ELO
df_plot = df.copy()
proba = model.predict_proba(df_plot.drop(columns=["home_win"]))[:, 1]
df_plot["home_prob"] = proba
df_plot["elo_diff"] = df_plot["elo_home"] - df_plot["elo_away"]

fig = px.scatter(df_plot, x="elo_diff", y="home_prob", title="Probabilidade (casa) vs Diferença de ELO")
st.plotly_chart(fig, use_container_width=True)

st.caption("MVP ok. Em seguida: API → DB → features reais + value bet.")
