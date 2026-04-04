# DigitalLogicHub-Graduation
# DigitalLogicHub

An intelligent recommender system for personalised learning materials in Digital Systems.  
Built by Malak Moqbel, Sara Ewaida, and Rand Awadallah — Birzeit University, 2026.

---

## What it does

DigitalLogicHub helps students learn Digital Systems (Boolean algebra, logic gates, sequential circuits, FSMs, Verilog HDL, and more) through:

- **VARK learning style assessment** — identifies whether you learn best visually, aurally, through reading, or hands-on
- **Skill assessment** — places you at beginner, intermediate, or advanced level
- **Hybrid recommender** — combines content-based and collaborative filtering to suggest the most relevant resources for your level, style, and known weak areas
- **Misconception tracking** — detects which concepts you keep getting wrong and pushes targeted resources to the top of your recommendations
- **Progress dashboard** — shows your scores, topic completion, and areas to improve

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 15 (Docker) |
| ORM / Migrations | SQLAlchemy, Alembic |
| Auth | JWT (python-jose), bcrypt (passlib) |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL)
- Python 3.12
- Node.js 18+

---

## Setup — step by step

### 1. Clone the repository

```bash
git clone https://github.com/your-org/DigitalLogicHub.git
cd DigitalLogicHub
```

### 2. Configure environment variables

```bash
cd backend
cp .env.example .env
```

Open `.env` and fill in your values. The defaults work for local development — only `EMAIL_USER` and `EMAIL_PASS` need real values (a Gmail account with an [App Password](https://support.google.com/accounts/answer/185833)).

### 3. Start the database

```bash
# From the project root (where docker-compose.yml lives)
docker compose up -d
```

Verify it's running:
```bash
docker ps
# Should show: digitallogichub_db   Up
```

### 4. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
cd backend
alembic upgrade head
```

This creates all tables. Run it once — re-running is safe (Alembic skips already-applied migrations).

### 6. Seed the VARK questions

```bash
cd backend
python3 seed_vark.py
```

This inserts the 16 VARK assessment questions. Safe to run multiple times — it skips if questions already exist.

### 7. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### 8. Start the frontend

```bash
cd frontend/my-app
npm install
npm start
```

The app opens at `http://localhost:3000`.

---

## Project structure

```
DigitalLogicHub/
├── docker-compose.yml          # PostgreSQL container
├── backend/
│   ├── .env.example            # Environment variable template
│   ├── requirements.txt        # Python dependencies
│   ├── seed_vark.py            # VARK question seed script
│   ├── alembic/                # Database migrations
│   │   └── versions/           # One file per migration
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── database.py         # SQLAlchemy engine + session
│       ├── dependencies.py     # get_db, get_current_user
│       ├── core/
│       │   └── jwt.py          # Token creation + verification
│       ├── models/             # SQLAlchemy table models
│       ├── api/                # Route handlers
│       │   ├── auth.py         # Register, login, verify, VARK
│       │   ├── assessment.py   # Skill quiz + misconception tracking
│       │   ├── recommender.py  # Hybrid recommendations + feedback
│       │   └── users.py        # Progress dashboard endpoint
│       ├── recommender/        # Recommendation engine
│       │   ├── content_based.py
│       │   ├── collaborative.py
│       │   ├── hybrid.py
│       │   └── utils.py
│       └── services/
│           └── email_service.py
└── frontend/
    └── my-app/
        ├── package.json
        └── src/
            ├── App.js
            ├── services/
            │   └── api.js      # Axios instance + JWT interceptor
            └── pages/          # React page components
```

---

## API overview

All endpoints except auth are protected — send `Authorization: Bearer <token>` in the request header. The frontend does this automatically via the Axios interceptor.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/verify` | Verify email + receive token |
| POST | `/auth/login` | Login + receive token |
| POST | `/auth/forgot` | Request password reset code |
| POST | `/auth/reset/password` | Set new password |
| GET | `/auth/vark/questions` | Load VARK quiz questions |
| POST | `/auth/vark/submit` | Submit VARK answers |
| GET | `/assessment/questions` | Load skill assessment questions |
| POST | `/assessment/submit` | Submit answers → sets level + detects misconceptions |
| GET | `/assessment/misconceptions/{user_id}` | Get user's misconception profile |
| GET | `/recommender/recommendations/{user_id}` | Get personalised resource list |
| POST | `/recommender/track/{user_id}/{resource_id}` | Record resource view |
| POST | `/recommender/feedback` | Submit rating / like / comment |
| GET | `/users/progress` | Dashboard: scores, topics, misconceptions |

---

## Database management

**Reset the database (destructive):**
```bash
docker compose down -v     # removes the volume (all data gone)
docker compose up -d       # fresh container
alembic upgrade head       # recreate schema
python3 seed_vark.py       # re-seed
```

**Connect with psql:**
```bash
psql postgresql://postgres:secret@localhost:5433/learner_db
```

**Check current migration:**
```bash
alembic current
```

---

## Common issues

**`ModuleNotFoundError: No module named 'app'`**  
Make sure you run `uvicorn` from inside the `backend/` directory, not the project root.

**`connection refused` on port 5433**  
Docker isn't running or the container hasn't started yet. Run `docker compose up -d` first.

**VARK quiz shows no questions**  
Run `python3 seed_vark.py` from inside `backend/`.

**JWT errors after pulling new code**  
Your old token may not match the new `JWT_SECRET`. Log out and log back in.

---

## Team

| Name | Student ID |
|---|---|
| Malak Moqbel | 1210608 |
| Sara Ewaida | 1203048 |
| Rand Awadallah | 1211963 |

Supervised by Dr. Abdellatif Abu-Issa — Birzeit University, Faculty of Engineering & Technology.