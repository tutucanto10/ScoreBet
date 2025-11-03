# >>> INÍCIO: src/ui/pages/1_🏀_NBA_Games.py
# Fix de path para rodar pelo Streamlit
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for p in (ROOT, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import pandas as pd
from sqlalchemy import select
from datetime import datetime, date, timedelta

from src.db.setup import SessionLocal
from src.db.models import NBAGame
from src.db.init_db import create_all
from src.api.nba_data import get_games
from src.db.upsert_games import upsert_nba_games

st.set_page_config(page_title="NBA Games", page_icon="🏀", layout="wide")
st.title("🏀 NBA — Jogos Recentes (Banco + API)")

# ---------- Helpers ----------
@st.cache_data(ttl=300)  # 5 min
def load_from_db() -> pd.DataFrame:
    create_all()
    with SessionLocal() as s:
        rows = s.execute(select(NBAGame)).scalars().all()
    if not rows:
        return pd.DataFrame(columns=["game_id","date","home_team","visitor_team","home_score","visitor_score","season"])
    df = pd.DataFrame([{
        "game_id": r.game_id,
        "date": pd.to_datetime(r.date),
        "home_team": r.home_team,
        "visitor_team": r.visitor_team,
        "home_score": r.home_score,
        "visitor_score": r.visitor_score,
        "season": r.season
    } for r in rows])
    return df

def kpi_block(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    total = len(df)
    avg_total_pts = (df["home_score"] + df["visitor_score"]).mean() if total else 0
    home_win = (df["home_score"] > df["visitor_score"]).mean() * 100 if total else 0
    recent_range = f'{df["date"].min().date()} → {df["date"].max().date()}' if total else "—"
    c1.metric("Jogos", f"{total}")
    c2.metric("Média Total Pontos", f"{avg_total_pts:.1f}")
    c3.metric("Vitórias dos mandantes", f"{home_win:.1f}%")
    c4.metric("Período mostrado", recent_range)

# ---------- Carregar e filtrar ----------
df_all = load_from_db()

with st.sidebar:
    st.header("Filtros")

    if df_all.empty:
        st.info("Banco vazio. Clique em **Atualizar/baixar** para popular.")
        default_start = date.today() - timedelta(days=7)
        default_end = date.today()
        seasons = []
        teams = []
    else:
        default_start = df_all["date"].min().date()
        default_end = df_all["date"].max().date()
        seasons = sorted(df_all["season"].unique().tolist())
        teams = sorted(pd.unique(pd.concat([df_all["home_team"], df_all["visitor_team"]])).tolist())

    d_start, d_end = st.date_input(
        "Intervalo de datas",
        value=(default_start, default_end),
        min_value=default_start if df_all.shape[0] else date.today() - timedelta(days=365),
        max_value=default_end if df_all.shape[0] else date.today()
    )

    sel_season = st.multiselect("Temporada", seasons, default=seasons)
    sel_teams = st.multiselect("Times (casa/fora)", teams, default=[])

    st.divider()
    st.subheader("Atualizar/baixar")
    days = st.number_input("Dias para baixar da API", min_value=1, max_value=60, value=7, step=1)
    if st.button("↻ Baixar e salvar jogos"):
        df_new = get_games(last_n_days=int(days))
        if df_new.empty:
            st.warning("Nenhum jogo retornado pela API.")
        else:
            n = upsert_nba_games(df_new)
            st.success(f"Upsert concluído: {n} linhas processadas.")
        st.cache_data.clear()

# aplica filtros
df = df_all.copy()
if not df.empty:
    df = df[(df["date"] >= pd.to_datetime(d_start)) & (df["date"] <= pd.to_datetime(d_end))]
    if sel_season:
        df = df[df["season"].isin(sel_season)]
    if sel_teams:
        df = df[(df["home_team"].isin(sel_teams)) | (df["visitor_team"].isin(sel_teams))]

# ---------- Exibir ----------
if df.empty:
    st.warning("Nenhum jogo para os filtros selecionados.")
else:
    kpi_block(df)

    st.subheader("Tabela de jogos")
    st.dataframe(
        df.sort_values(["date", "game_id"], ascending=[False, True])
          .assign(date=lambda x: x["date"].dt.strftime("%Y-%m-%d")),
        use_container_width=True
    )

    st.subheader("Pontos por dia (Total)")
    tmp = df.copy()
    tmp["total_pts"] = tmp["home_score"] + tmp["visitor_score"]
    tmp = tmp.groupby(tmp["date"].dt.date, as_index=False)["total_pts"].mean()
    tmp = tmp.sort_values("date")
    st.line_chart(tmp.set_index("date")["total_pts"])

    st.subheader("Distribuição de placares (Home x Visitor)")
    st.bar_chart(df[["home_score", "visitor_score"]])

# >>> FIM
