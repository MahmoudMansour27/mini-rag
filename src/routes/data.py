from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Setting
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal, ProjectModel, ChunkModel, DataChunkEntry
from .schemes.data import ProcessRequest

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


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id:str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = ProjectModel(db_client=request.app.state.db_client)
    project = await project_model.get_or_create_project(project_id=project_id)

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)
    if file_content is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.UNSPORRTED_FILE_TYPE.value,
            }
        )


    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        chunk_overlap=overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value,
            }
        )
    
    file_chunks_records = [
        DataChunkEntry(
            chunk_text=chunk.page_content,
            chunk_metadata= chunk.metadata,
            chunk_order=i + 1,
            chunk_project_id= project.id
         
        )
        for i, chunk in enumerate(file_chunks)
    ]

    chunk_model = ChunkModel(db_client=request.app.state.db_client)

    if do_reset:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.project_id)

    no_records = await chunk_model.create_many_chunks(chunks=file_chunks_records)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "no_records": f"Total {no_records} chunks have been created."
        }
    )
    





    


