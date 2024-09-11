from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src.auth.router import router as auth_router
from src.companies.router import router as company_router
from src.quizzes.router import router as quizzes_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(company_router)
app.include_router(quizzes_router)

add_pagination(app)

@app.get("/healthy")
def health_check():
    return {
        "status_code": 200,
        "detail": "ok",
        "result": "working"
    }
