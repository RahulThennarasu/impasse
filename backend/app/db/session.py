from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

class Settings(BaseSettings):
    database_url: str = os.getenv("SUPABASE_DB_URL")
    
    class Config:
        env_file = ".env"

settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
