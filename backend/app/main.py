import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# ── Task 7: Startup env validation ────────────────────────────────────────────
REQUIRED_ENV_VARS = {
    "DATABASE_URL": "PostgreSQL connection string, e.g. postgresql://user:pass@localhost/dbname",
    "SECRET_KEY":   "JWT signing secret — generate with: openssl rand -hex 32",
    "EMAIL_USER":   "Gmail address used to send verification emails, e.g. yourapp@gmail.com",
    "EMAIL_PASS":   "Gmail App Password (NOT your regular password). "
                    "Generate at https://myaccount.google.com/apppasswords",
}

missing = {k: v for k, v in REQUIRED_ENV_VARS.items() if not os.getenv(k)}
if missing:
    lines = [
        "",
        "=" * 60,
        "  STARTUP FAILED — missing required environment variables",
        "=" * 60,
    ]
    for var, hint in missing.items():
        lines.append(f"\n  ❌  {var}")
        lines.append(f"      → {hint}")
    lines += [
        "",
        "  Add the missing variables to your .env file and restart.",
        "  See .env.example for a full template.",
        "=" * 60,
        "",
    ]
    print("\n".join(lines), file=sys.stderr)
    sys.exit(1)
# ──────────────────────────────────────────────────────────────────────────────

from app.api import auth
from app.api import assessment
from app.api import recommender
from app.api import users          # ← new
from app.api import resource_quiz  # ← new

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
app.include_router(resource_quiz.router, prefix="/quiz",      tags=["Resource Quiz"])


@app.get("/")
def root():
    return {"message": "DigitalLogicHub backend running 🚀"}