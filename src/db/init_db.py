# >>> INÍCIO PATCH: src/db/init_db.py
from src.db.setup import engine
from src.db.models import Base

def create_all():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_all()
    print("Tabelas criadas.")
# >>> FIM PATCH
