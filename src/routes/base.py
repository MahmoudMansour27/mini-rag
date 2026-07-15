from helpers.config import get_settings
from fastapi import FastAPI, APIRouter
import os

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)


@base_router.get("/")
async def welcome():
    app_setting = get_settings()

    return {
        "message": f"Welcome to {app_setting.APP_NAME} API!",
        "version": app_setting.APP_VERSION,
        "allowed_file_types": app_setting.FILE_ALLOWED_TYPES,
    }