# scorebet/src/api/nba_data.py
from __future__ import annotations
import requests
import pandas as pd
from datetime import date, timedelta
from typing import Iterable, List
from src.utils.logger import get_logger
from src.utils.config import settings

logger = get_logger("nba_api")

def _headers() -> dict:
    """
    A balldontlie (host api.balldontlie.io) exige API key.
    Enviamos nos dois formatos mais comuns por compatibilidade.
    """
    if settings.BDL_API_KEY:
        return {
            "Authorization": f"Bearer {settings.BDL_API_KEY}",
            "X-API-KEY": settings.BDL_API_KEY,
        }
    return {}

def _fetch_games_for_dates(dates: List[str]) -> pd.DataFrame:
    """
    Busca jogos usando dates[] (enviado N vezes) com paginação.
    Retorna colunas padronizadas para o resto do pipeline.
    """
    all_rows, page = [], 1
    while True:
        # Atenção: precisa ser lista de tuplas para repetir 'dates[]'
        params = [("per_page", 100), ("page", page)]
        for d in dates:
            params.append(("dates[]", d))

        url = "https://api.balldontlie.io/v1/games"
        logger.info(f"GET {url} page={page} dates={dates}")
        resp = requests.get(url, params=params, headers=_headers(), timeout=20)

        if resp.status_code != 200:
            logger.error(f"HTTP {resp.status_code} em {resp.url}")
            logger.error(f"Body: {resp.text[:400]}")
            resp.raise_for_status()

        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            break

        for g in data:
            all_rows.append({
                "game_id": g["id"],
                "date": g["date"][:10],
                "home_team": g["home_team"]["full_name"],
                "visitor_team": g["visitor_team"]["full_name"],
                "home_score": g["home_team_score"],
                "visitor_score": g["visitor_team_score"],
                "season": g["season"],
            })

        meta = payload.get("meta", {})
        if page < meta.get("total_pages", 1):
            page += 1
        else:
            break

    return pd.DataFrame(all_rows)

def get_games(last_n_days: int = 3) -> pd.DataFrame:
    """
    Coleta jogos dos últimos 'last_n_days' dias (inclui hoje).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=last_n_days)
    dates = [(start_date + timedelta(days=i)).isoformat()
             for i in range((end_date - start_date).days + 1)]
    logger.info(f"Baixando jogos NBA (dates[]: {dates[0]} .. {dates[-1]})")
    try:
        df = _fetch_games_for_dates(dates)
        if df.empty:
            logger.warning("Nenhum jogo encontrado para o intervalo informado.")
        else:
            logger.info(f"{len(df)} jogos coletados.")
        return df
    except Exception as e:
        logger.error(f"Erro ao coletar dados NBA: {e}")
        return pd.DataFrame()

def get_games_by_dates(dates: Iterable[str]) -> pd.DataFrame:
    """
    Coleta jogos informando datas exatas (iterável de 'YYYY-MM-DD').
    Útil para testes com datas conhecidas.
    """
    dates = list(dates)
    logger.info(f"Baixando jogos NBA para datas específicas: {dates}")
    try:
        df = _fetch_games_for_dates(dates)
        if df.empty:
            logger.warning("Nenhum jogo retornado para as datas fornecidas.")
        else:
            logger.info(f"{len(df)} jogos coletados.")
        return df
    except Exception as e:
        logger.error(f"Erro ao coletar por datas: {e}")
        return pd.DataFrame()
def get_upcoming_games(days_ahead: int = 3) -> pd.DataFrame:
    """
    Jogos futuros (agendados) para os próximos N dias usando balldontlie.
    Retorna DF com: game_id, date, season, home_team, visitor_team.
    """
    logger = get_logger("nba_api")
    start = date.today()
    end = start + timedelta(days=days_ahead)
    dates = [(start + timedelta(i)).isoformat() for i in range((end - start).days + 1)]

    all_rows = []
    page = 1
    while True:
        params = [("per_page", 100), ("page", page)]
        for d in dates:
            params.append(("dates[]", d))
        url = "https://api.balldontlie.io/v1/games"
        headers = {}
        if settings.BDL_API_KEY:
            headers = {"Authorization": f"Bearer {settings.BDL_API_KEY}", "X-API-KEY": settings.BDL_API_KEY}
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            break
        for g in data:
            # jogos futuros chegam com scores 0, status 'Scheduled'
            all_rows.append({
                "game_id": g["id"],
                "date": g["date"][:10],
                "season": g["season"],
                "home_team": g["home_team"]["full_name"],
                "visitor_team": g["visitor_team"]["full_name"],
            })
        meta = payload.get("meta", {})
        if page < meta.get("total_pages", 1):
            page += 1
        else:
            break

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["game_id"]).sort_values("date")
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df