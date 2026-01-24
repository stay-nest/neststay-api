"""FastAPI application entry point."""
from fastapi import FastAPI, Depends
from sqlmodel import Session
from database import get_session

app = FastAPI(
    title="NestStay API",
    description="API for NestStay application",
    version="0.1.0"
)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to NestStay API"}


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}
