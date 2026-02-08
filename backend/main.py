"""
Insight Stream API - Main Application Entry Point

A YouTube video summarization service using AI.
Extracts transcripts and generates intelligent summaries.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.core.config import settings
from app.api.endpoints import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info(f"🚀 {settings.APP_TITLE} v{settings.APP_VERSION} starting...")
    logger.info(f"📍 Allowed origins: {settings.ALLOWED_ORIGINS}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    logger.info(f"🛑 {settings.APP_TITLE} shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="YouTube video transcript extraction and AI-powered summarization API",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
