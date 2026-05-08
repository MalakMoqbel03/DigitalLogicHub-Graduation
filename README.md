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
- **AI-powered personalised quizzes** — after each resource, OpenAI GPT generates 2 fresh multiple-choice questions tailored to the student's level, known misconceptions, and study history; wrong answers trigger an AI explanation and update the misconception profile
- **Misconception improvement tracking** — quiz questions are deliberately designed to re-probe past misconceptions so the system can detect whether they have been corrected over time
- **Bookmark / Save resources** — users can save any resource for later from the resource viewer
- **Resource feedback** — star rating, like/dislike, and free-text comment on every resource
- **Progress dashboard** — shows your scores, topic completion, and areas to improve
- **Adaptive level progression** — level (beginner → intermediate → advanced) is automatically updated based on a rolling window of the last 20 quiz answers

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 15 (Docker) |
| ORM / Migrations | SQLAlchemy, Alembic |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Quiz AI | OpenAI GPT-4o-mini |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL)
- Python 3.12
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys) (for personalised quiz generation)

---

## Setup — step by step

### 1. Clone the repository

```bash
git clone https://github.com/MalakMoqbel03/DigitalLogicHub-Graduation.git
cd DigitalLogicHub
```

### 2. Configure environment variables

```bash
cd backend
cp .env.example .env
```

Open `.env` and fill in your values:

```env
# Database (defaults work for local Docker setup)
DATABASE_URL=postgresql://postgres:secret@localhost:5433/learner_db

# JWT
JWT_SECRET=your_secret_key_here

# Email (Gmail + App Password)
EMAIL_USER=your@gmail.com
EMAIL_PASS=your_app_password

# OpenAI — required for AI quiz generation
OPENAI_API_KEY=sk-...
```

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

This creates all tables including `resource_quiz_questions`, `user_resource_quiz_attempts`, `user_misconceptions`, and the `is_bookmarked` / `is_skipped` columns on `user_learning_resources`. Run it once — re-running is safe.

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
├── docker-compose.yml               # PostgreSQL container
├── backend/
│   ├── .env.example                 # Environment variable template
│   ├── requirements.txt             # Python dependencies
│   ├── seed_vark.py                 # VARK question seed script
│   ├── alembic/                     # Database migrations
│   │   └── versions/                # One file per migration
│   └── app/
│       ├── main.py                  # FastAPI app entry point
│       ├── database.py              # SQLAlchemy engine + session
│       ├── dependencies.py          # get_db, get_current_user
│       ├── core/
│       │   └── jwt.py               # Token creation + verification
│       ├── models/
│       │   ├── user.py
│       │   ├── learning_resource.py
│       │   ├── user_learning_resource.py   # bookmarked + skipped flags
│       │   ├── user_misconception.py       # concept_tag + count tracking
│       │   ├── resource_quiz.py            # quiz questions + attempt records
│       │   ├── user_resource_feedback.py
│       │   ├── assessment.py
│       │   └── vark.py
│       ├── api/
│       │   ├── auth.py              # Register, login, verify, VARK
│       │   ├── assessment.py        # Skill quiz + misconception tracking
│       │   ├── recommender.py       # Hybrid recommendations, feedback, bookmarks
│       │   ├── resource_quiz.py     # AI quiz generation + submission
│       │   └── users.py            # Progress dashboard endpoint
│       ├── recommender/
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
            │   └── api.js           # Axios instance + JWT interceptor
            └── pages/
                ├── ResourceViewer.jsx   # Resource embed, quiz, bookmark, feedback
                ├── LearningMaterials.jsx
                └── ...
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
| GET | `/recommender/feedback/{user_id}/{resource_id}` | Get existing feedback for a resource |
| POST | `/recommender/bookmark` | Save or unsave a resource |
| GET | `/recommender/bookmarks/{user_id}` | Get all bookmarked resources |
| GET | `/quiz/questions/{resource_id}?user_id=` | Generate 2 personalised AI quiz questions |
| POST | `/quiz/submit` | Submit answers → updates misconceptions + level |
| GET | `/quiz/history/{user_id}/{resource_id}` | Check if user already attempted quiz |
| GET | `/users/progress` | Dashboard: scores, topics, misconceptions |

---

## How the AI quiz works

When a student finishes a resource and clicks **Take Quiz**, the backend:

1. Fetches the student's current **level** (beginner / intermediate / advanced) from their profile.
2. Fetches their **top misconceptions** from `user_misconceptions` — the concept tags they have answered wrong most frequently, with counts.
3. Fetches the **topics of all resources** they have previously attempted, so the prompt knows what prior knowledge to assume.
4. Sends all of this — together with the resource's title, topic, subtopic, and description — to **OpenAI GPT-4o-mini** with a carefully structured prompt.

The prompt instructs GPT to:
- Match question difficulty to the student's level.
- Write at least one question that **directly probes an active misconception** — with a wrong option that reflects exactly how a student with that misconception would reason, so a correct answer proves the misconception is resolved.
- Return strict JSON (2 questions, 4 options each, one correct answer, a `concept_tag` per question).

On submission:
- Wrong answers increment the `count` on the relevant `UserMisconception` row.
- GPT generates a short, encouraging explanation for each wrong answer.
- The resource is marked as viewed.
- The student's level is re-evaluated against the last 20 answers (≥ 80% correct → promote, ≤ 40% → demote).

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

**Quiz returns 500 — `column user_learning_resources.is_bookmarked does not exist`**  
Your database schema is out of date. Run `alembic upgrade head` to apply the latest migrations.

**Quiz questions are generic / not personalised**  
Make sure `OPENAI_API_KEY` is set in your `.env` file. Check the backend logs for `[quiz]` lines to confirm GPT is being called.

**Resource viewer shows a gray empty box**  
The resource is a non-embeddable type (article, website, etc.). This is expected — the viewer now shows a rich resource card with description, metadata, and an "Open" button instead of a broken iframe.

---

## Team

| Name | Student ID |
|---|---|
| Malak Moqbel | 1210608 |
| Sara Ewaida | 1203048 |
| Rand Awadallah | 1211963 |

Supervised by Dr. Abdellatif Abu-Issa — Birzeit University, Faculty of Engineering & Technology.
