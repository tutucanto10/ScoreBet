# ... resto igual
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    BDL_API_KEY: str | None = os.getenv("BDL_API_KEY")
    ODDS_API_KEY: str | None = os.getenv("ODDS_API_KEY")
    API_SPORTS_KEY: str | None = os.getenv("API_SPORTS_KEY")  # <-- ADICIONE ESTA LINHA
    DB_URL: str = os.getenv("DB_URL", "sqlite:///scorebet.db")

settings = Settings()

