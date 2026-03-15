from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, JSONResponse
from contextlib import asynccontextmanager
from app.config.database import Base, engine
from app.api.auth_routes import router as auth_router
from app.api.file_routes import router as file_router
from app.api.social_routes import router as social_router
from app.api.content_gen_routes import router as content_gen_router
from app.config.redis import init_redis, close_redis
from app.messaging.rabbitmq import connect_rabbitmq, close_rabbitmq
from app.messaging.consumer import start_consumer
from app.services.exceptions import AppBaseException
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await init_redis()
    await connect_rabbitmq()
    await start_consumer()

    yield

    await close_redis()
    await close_rabbitmq()


app = FastAPI(
    title="Nexus — Async AI Document & Content Engine",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)


@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(auth_router)
app.include_router(file_router)
app.include_router(content_gen_router)
app.include_router(social_router)