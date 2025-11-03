from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.config import settings

engine = create_engine(settings.DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Fornece uma sessão de banco de dados para operações locais."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
