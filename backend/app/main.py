import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.api import auth
from app.api import assessment
from app.api import recommender
from app.api import users          # ← new

app = FastAPI(title="DigitalLogicHub API")

# ── CORS ──────────────────────────────────────────────────────────────────────
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
app.include_router(assessment.router,  prefix="/assessment",  tags=["Assessment"])
app.include_router(recommender.router, prefix="/recommender", tags=["Recommender"])
app.include_router(users.router,       prefix="/users",       tags=["Users"])


@app.get("/")
def root():
    return {"message": "DigitalLogicHub backend running 🚀"}