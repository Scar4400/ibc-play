import os
from main import engine, Base
from alembic.config import Config
from alembic import command

def init_db():
    print("Initializing database...")
    if os.path.exists("alembic/versions"):
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        print("Alembic migrations applied.")
    else:
        Base.metadata.create_all(bind=engine)
        print("Tables created via create_all (dev only).")
    print("Database ready.")

if __name__ == "__main__":
    init_db()