from dotenv import load_dotenv
from fastapi import FastAPI
from app.db.db import create_tables
from contextlib import asynccontextmanager
from app import models  # noqa: F401
from app.handlers.v1.signup import router as signup_router
from app.handlers.v1.verify import router as verify_router
from app.handlers.v1.login import router as login_router
from app.handlers.v1.refresh import router as refresh_router
from app.handlers.v1.logout import router as logout_router
from app.handlers.v1.resend import router as resend_router
from app.handlers.v1.forgot_password import router as forgot_password_router
from app.handlers.v1.reset_password import router as reset_password_router


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(signup_router, prefix="/api/v1")
app.include_router(resend_router, prefix="/api/v1")
app.include_router(verify_router, prefix="/api/v1")
app.include_router(refresh_router, prefix="/api/v1")
app.include_router(login_router, prefix="/api/v1")
app.include_router(logout_router, prefix="/api/v1")
app.include_router(forgot_password_router, prefix="/api/v1")
app.include_router(reset_password_router, prefix="/api/v1")
