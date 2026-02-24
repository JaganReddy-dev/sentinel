from dotenv import load_dotenv
from fastapi import FastAPI
from app.db.db import create_tables
from contextlib import asynccontextmanager
from app import models  # noqa: F401
from app.handlers.v1.signup import router as signup_router
from app.handlers.v1.verify import router as verify_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(signup_router, prefix="/api/v1")
app.include_router(verify_router, prefix="/api/v1")
