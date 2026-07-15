from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Setting
from controllers import DataController, ProjectController
import aiofiles
from models import ResponseSignal

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,
                      app_settings: Setting = Depends(get_settings)):
    

    # validate file prop
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )
    
    project_dir = ProjectController().get_project_path(project_id= project_id)
    file_path, file_id = data_controller.generate_file_path(
        org_file_name=file.filename,
        project_id=project_id
    )

    # Save the uploaded file to the generated file path
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):  # Read the file in chunks
                await out_file.write(chunk)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value,
                "error": str(e)
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "file_path": file_path
            }
        )

    


    


