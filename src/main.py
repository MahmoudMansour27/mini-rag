from fastapi import FastAPI
from dotenv import load_dotenv
from routes.base import base_router
from routes.data import data_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager
from stores.llm.LLMFactory import LLMProviderFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.mongo_connection = AsyncIOMotorClient(settings.MONGO_URI)
    app.state.db_client = app.state.mongo_connection[settings.MONGO_DATABASE_NAME]

    llm_provider_factory = LLMProviderFactory(settings)

    # set generation client
    app.state.generation_client = llm_provider_factory.create(provider= settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(model_id= settings.GENERATION_MODEL_ID)

    # set embedding client
    app.state.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(
        model_id= settings.EMBEDDING_MODEL_ID,
        embedding_size= settings.EMBEDDING_MODEL_SIZE
        )
    

    # closing
    yield
    app.state.mongo_connection.close()

app = FastAPI(lifespan=lifespan)

app.include_router(base_router)
app.include_router(data_router)