# scorebet/src/db/upsert_games.py
from typing import Iterable
import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import text
from src.db.setup import engine, SessionLocal
from src.db.models import NBAGame

# --- helpers ---------------------------------------------------------------

_INT_COLS = ["game_id", "home_score", "visitor_score", "season"]
_BASE_COLS = ["game_id", "date", "home_team", "visitor_team", "home_score", "visitor_score", "season"]

def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos para o ORM (SQLite exige date real)."""
    out = df.copy()

    # date -> datetime.date
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date

    # inteiros garantidos
    for c in _INT_COLS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype(int)

    # strings básicas
    for c in ["home_team", "visitor_team"]:
        if c in out.columns:
            out[c] = out[c].astype(str)

    return out

def _df_to_rows(df: pd.DataFrame):
    df = _coerce_types(df)
    missing = [c for c in _BASE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes para upsert: {missing}")
    return df[_BASE_COLS].to_dict(orient="records")

# --- upsert ----------------------------------------------------------------

def upsert_nba_games(df: pd.DataFrame) -> int:
    """Upsert em lote de jogos da NBA.
    - SQLite: usa ON CONFLICT (game_id).
    - Outros bancos: fallback com merge linha-a-linha (portável).
    Retorna um número aproximado de linhas afetadas.
    """
    if df.empty:
        return 0

    rows = _df_to_rows(df)

    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            stmt = sqlite_insert(NBAGame).values(rows)
            update_cols = {c: stmt.excluded[c] for c in _BASE_COLS if c != "game_id"}
            stmt = stmt.on_conflict_do_update(
                index_elements=[NBAGame.game_id],
                set_=update_cols
            )
            result = conn.execute(stmt)
            affected = result.rowcount or 0
            if affected == 0:
                conn.execute(text("SELECT 1"))
            return affected
        else:
            # Fallback portável
            from sqlalchemy.orm import Session
            with Session(bind=conn) as s:
                for r in rows:
                    s.merge(NBAGame(**r))
                s.commit()
                return len(rows)
