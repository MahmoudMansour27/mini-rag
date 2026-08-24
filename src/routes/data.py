from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Setting
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal, ProjectModel, ChunkModel, DataChunkEntry
from .schemes.data import ProcessRequest
from models import AssetModel, Asset, AssetTypesEnum
from models import ProjectModel, ChunkModel

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile,
                      app_settings: Setting = Depends(get_settings)):
    

    # init projects collection
    project_model = await ProjectModel.create_instance(db_client=request.app.state.db_client)

    project = await project_model.get_or_create_project(project_id=project_id)

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
    
    # store asset in db
    asset_model = await AssetModel.create_instance(db_client=request.app.state.db_client) 

    asset_entry = Asset(
        asset_project_id= project.id,
        asset_type = AssetTypesEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset= asset_entry)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.id),
            }
        )


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id:str, process_request: ProcessRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    # init collections
    project_model = await ProjectModel.create_instance(db_client=request.app.state.db_client)
    project = await project_model.get_or_create_project(project_id=project_id)
    asset_model = await AssetModel.create_instance(db_client=request.app.state.db_client) 

    # get all related assets
    project_files_ids = {}

    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id= project.id,
            asset_name= process_request.file_id
        )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                }
            )
        project_files_ids = {
            asset_record.id : asset_record.asset_name
        }
    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id= project.id,
            asset_type= AssetTypesEnum.FILE.value
        )

        project_files_ids = {
            record.id : record.asset_name
            for record in project_files
        }

    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
            }
        )    
    

    # processing 
    process_controller = ProcessController(project_id=project_id)
    no_records = 0
    no_files = 0

    chunk_model = await ChunkModel.create_instance(db_client=request.app.state.db_client)

    if do_reset:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.id)


    for asset_id, file_id in project_files_ids:

        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            print(f"Failed to read file content for file_id: {file_id}")
            continue

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
    
        no_records = await chunk_model.create_many_chunks(chunks=file_chunks_records)
        no_files += 1

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "no_records": f"Total {no_records} chunks have been created.",
            "no_files": f"Total {no_files} files have been processed."
        }
    )
    





    


