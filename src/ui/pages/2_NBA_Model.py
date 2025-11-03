import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="🧠 ScoreBet — Modelo NBA", page_icon="🧠", layout="wide")
st.title("🧠 ScoreBet — Treinamento do Modelo")

st.caption("Simulação de treinamento e avaliação do modelo de predição de resultados da NBA.")

with st.spinner("Treinando modelo..."):
    time.sleep(2)
    accuracy = round(np.random.uniform(0.72, 0.88), 3)
    recall = round(np.random.uniform(0.65, 0.83), 3)
    precision = round(np.random.uniform(0.70, 0.86), 3)
    f1 = round((2 * precision * recall) / (precision + recall), 3)
st.success("Modelo treinado com sucesso!")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Acurácia", f"{accuracy*100:.1f}%")
col2.metric("Precisão", f"{precision*100:.1f}%")
col3.metric("Recall", f"{recall*100:.1f}%")
col4.metric("F1-Score", f"{f1*100:.1f}%")

st.subheader("📊 Importância de Recursos (simulada)")
feat = pd.DataFrame({
    "Feature": ["Home Win %", "Away Win %", "Avg Points Home", "Avg Points Away", "Últimos confrontos"],
    "Importância": np.random.uniform(0.1, 1.0, 5)
}).sort_values("Importância", ascending=False)

st.bar_chart(feat.set_index("Feature"))
st.caption("Os valores acima são simulados para exibição visual. O modelo real será conectado posteriormente.")
