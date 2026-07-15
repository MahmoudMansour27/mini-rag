from fastapi import FastAPI
from dotenv import load_dotenv
from routes.base import base_router
from routes.data import data_router

load_dotenv(".env")


app = FastAPI()
app.include_router(base_router)
app.include_router(data_router)