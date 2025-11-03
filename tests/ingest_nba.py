# >>> INÍCIO PATCH: tests/ingest_nba.py
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from datetime import datetime
from src.api.nba_data import get_games
from src.db.init_db import create_all
from src.db.upsert_games import upsert_nba_games

if __name__ == "__main__":
    create_all()
    df = get_games(last_n_days=7)
    if df.empty:
        print("Nenhum jogo coletado.")
        raise SystemExit(0)
    n = upsert_nba_games(df)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upsert concluído. Linhas processadas: {n}")
# >>> FIM PATCH
