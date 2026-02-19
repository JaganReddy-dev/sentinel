# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("DB_URL")
if DB_URL is None:
    raise ValueError("DB_URL_Read_Error")

engine = create_engine(
    DB_URL, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
