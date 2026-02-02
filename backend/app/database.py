from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# load .env relative to backend folder
base_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)   # <-- TEMP DEBUG

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
