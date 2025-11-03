# >>> INÍCIO PATCH: src/db/models.py
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Date

Base = declarative_base()

class NBAGame(Base):
    __tablename__ = "nba_games"

    game_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, index=True)
    home_team: Mapped[str] = mapped_column(String(80), index=True)
    visitor_team: Mapped[str] = mapped_column(String(80), index=True)
    home_score: Mapped[int] = mapped_column(Integer)
    visitor_score: Mapped[int] = mapped_column(Integer)
    season: Mapped[int] = mapped_column(Integer, index=True)
# >>> FIM PATCH
