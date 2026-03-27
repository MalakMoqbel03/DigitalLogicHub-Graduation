from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.api import assessment
from app.api import recommender
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.109:3000",  # <-- YOUR ACTUAL FRONTEND
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(assessment.router, prefix="/assessment", tags=["Assessment"])
app.include_router(recommender.router, prefix="/recommender", tags=["Recommender"])
@app.get("/")
def root():
    return {"message": "DigitalLogicHub backend running 🚀"}
