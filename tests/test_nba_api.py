# scorebet/tests/test_nba_api.py
import sys, pathlib, importlib.util, inspect

ROOT = pathlib.Path(__file__).resolve().parents[1]   # .../scorebet
SRC = ROOT / "src"                                   # .../scorebet/src
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

print("DEBUG ROOT:", ROOT)
print("DEBUG SRC exists:", SRC.exists(), "nba_data.py exists:", (SRC / "api" / "nba_data.py").exists())

# Tenta import normal; se falhar, carrega direto do arquivo
try:
    from api.nba_data import get_games, get_games_by_dates
    import api.nba_data as nd
    print("DEBUG MODULE FILE (import):", inspect.getfile(nd))
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location("nba_data", SRC / "api" / "nba_data.py")
    nd = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(nd)
    get_games = nd.get_games
    get_games_by_dates = nd.get_games_by_dates
    print("DEBUG MODULE FILE (direct):", SRC / "api" / "nba_data.py")

print("DEBUG URL check in file:", "balldontlie.io/api/v1/games" in open(SRC / "api" / "nba_data.py", "r", encoding="utf-8").read())

if __name__ == "__main__":
    print("=== TESTE 1: datas fixas conhecidas (deve retornar jogos) ===")
    known_dates = ["2024-10-24", "2024-10-25", "2024-10-26"]
    df_fixed = get_games_by_dates(known_dates)
    print(df_fixed.head())
    print(f"Total (datas fixas): {len(df_fixed)}\n")

    print("=== TESTE 2: últimos 5 dias a partir de hoje ===")
    df_recent = get_games(last_n_days=5)
    print(df_recent.head())
    print(f"Total (últimos dias): {len(df_recent)}")
