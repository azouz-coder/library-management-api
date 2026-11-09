from sqlalchemy import create_engine,URL
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()
DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT","5432")
DB_NAME=os.getenv("DB_NAME") 
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
database_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)
engine = create_engine(database_url)
def create_db_engine(path):
    return create_engine(f"sqlite:///{path}")
def create_session_factory(engine):
    return sessionmaker(bind=engine)
SessionLocal = sessionmaker(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

