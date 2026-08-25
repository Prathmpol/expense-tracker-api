"""
FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Docs available at /docs (Swagger UI) and /redoc.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, expenses, income, analytics

# Creates tables if they don't exist yet. For production use, prefer Alembic
# migrations (see alembic/ directory) instead of relying on this.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A backend API for tracking personal income/expenses and generating "
        "financial analytics: totals, category breakdowns, monthly trends, "
        "and savings rate."
    ),
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(income.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
