# db_init.py
from main import engine, Base
import os

def init_db():
    print("Creating database tables (if missing)...")
    Base.metadata.create_all(bind=engine)
    print("Done. Database tables created/verified.")

if __name__ == "__main__":
    init_db()
