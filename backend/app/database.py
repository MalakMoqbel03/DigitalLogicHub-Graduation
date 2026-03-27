from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# load .env relative to backend folder
base_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)   # helpful debug when starting server

if not DATABASE_URL:
	raise RuntimeError("DATABASE_URL is not set. Create a .env with DATABASE_URL.")

try:
	engine = create_engine(DATABASE_URL)
except Exception as e:
	# Provide a clearer error message at import time to avoid confusing ImportErrors
	print("Failed to create SQLAlchemy engine:", e)
	raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
