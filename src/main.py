from fastapi import FastAPI
from dotenv import load_dotenv
from routes.base import base_router
from routes.data import data_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.mongo_connection = AsyncIOMotorClient(settings.MONGO_URI)
    app.state.db_client = app.state.mongo_connection[settings.MONGO_DATABASE_NAME]
    yield
    app.state.mongo_connection.close()

app = FastAPI(lifespan=lifespan)

app.include_router(base_router)
app.include_router(data_router)