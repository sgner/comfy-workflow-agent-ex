from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.config import settings
from backend.routes import chat, workflow, actions, config
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ComfyUI Workflow Agent API...")
    logger.info(f"Checkpoint directory: {settings.CHECKPOINT_DIR}")
    logger.info(f"Database directory: {settings.DATABASE_DIR}")
    from backend.config import ensure_directories
    ensure_directories()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="ComfyUI Workflow Agent API",
    description="Backend API for ComfyUI Workflow Agent with LangGraph and FastMCP",
    version="1.2.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(config.router, prefix="/api", tags=["Config"])


@app.get("/")
async def root():
    return {
        "message": "ComfyUI Workflow Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
