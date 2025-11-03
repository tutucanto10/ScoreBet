# src/db/setup.py
# >>> INÍCIO PATCH: src/db/setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import settings

# Default: SQLite no arquivo scorebet.db na raiz do projeto
DB_URL = settings.DB_URL or "sqlite:///scorebet.db"

# check_same_thread=False para evitar erro no Streamlit/threads com SQLite
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
# >>> FIM PATCH

