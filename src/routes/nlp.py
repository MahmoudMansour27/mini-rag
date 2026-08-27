from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from controllers.NLPController import NLPController
from models.enums import ResponseSignal
from schemes.nlp import PushRequest, SearchRequest

nlp_router = APIRouter(
    prefix= "/api/v1/nlp",
    tags= ["api_v1","nlp"]
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.state.db_client
    )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.state.db_client
    )

    project = await project_model.get_or_create_project(
        project_id= project_id
    )

    if not project:
        return JSONResponse(
            status_code= status.HTTP_404_NOT_FOUND,
            content= {
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value,
                "message": f"Project with ID {project_id} not found."
            }
        )

    nlp_controller = NLPController(
        vectordb_client= request.app.state.vectordb_client,
        generation_client= request.app.state.generation_client,
        embedding_client= request.app.state.embedding_client,
        template_parser= request.app.state.template_parser
    )

    # indexing
    has_records = True
    page_no = 1
    inserted_items_count = 0
    idx = 0
    while has_records:
        page_chunks = await chunk_model.get_project_chunks(
            project_id= project_id,
            page_no= page_no,

        )

        if len(page_chunks):
            page_no += 1

        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        chunks_ids = list(range(idx, idx+len(page_chunks)))
        idx += len(page_chunks)

        is_inserted = nlp_controller.index_into_vector_db(
            project= project,
            chunks= page_chunks,
            chunks_ids= chunks_ids,
            do_reset= push_request.do_reset
        )

        if not is_inserted:
            return JSONResponse(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                content= {
                    "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value,
                    "message": f"Failed to index chunks for project {project_id}."
                }
            )
        inserted_items_count += len(page_chunks)

    return JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {
            "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
            "message": f"Successfully indexed {inserted_items_count} chunks for project {project_id}.",
            "indexed_count": inserted_items_count
        }
    )

@nlp_router.post("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.state.db_client
    )
    project = await project_model.get_or_create_project(
        project_id= project_id
    )
    nlp_controller = NLPController(
        vectordb_client= request.app.state.vectordb_client,
        generation_client= request.app.state.generation_client,
        embedding_client= request.app.state.embedding_client,
        template_parser= request.app.state.template_parser
    )

    collection_info = nlp_controller.get_vector_db_collection_info(
        project= project
    )

    return JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {
            "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
            "message": f"Retrieved collection info for project {project_id}.",
            "collection_info": collection_info
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.state.db_client
    )
    project = await project_model.get_or_create_project(
        project_id= project_id
    )
    nlp_controller = NLPController(
        vectordb_client= request.app.state.vectordb_client,
        generation_client= request.app.state.generation_client,
        embedding_client= request.app.state.embedding_client,
        template_parser= request.app.state.template_parser
    )

    results = nlp_controller.search_vector_db_collection(
        project= project,
        text= search_request.text,
        limit= search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code= status.HTTP_404_NOT_FOUND,
            content= {
                "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value,
                "message": f"No results found for the search query in project {project_id}."
            }
        )

    return JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {
            "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "message": f"Search results for project {project_id}.",
            "results": [ result.dict()  for result in results ]
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.state.db_client
    )
    project = await project_model.get_or_create_project(
        project_id= project_id
    )
    nlp_controller = NLPController(
        vectordb_client= request.app.state.vectordb_client,
        generation_client= request.app.state.generation_client,
        embedding_client= request.app.state.embedding_client,
        template_parser= request.app.state.template_parser
    )

    answer, full_prompt, chat_history = nlp_controller.answer_rag_question(
        project= project,
        query= search_request.text,
        limit= search_request.limit
    ) 

    if not answer:
        return JSONResponse(
            status_code= status.HTTP_404_NOT_FOUND,
            content= {
                "signal": ResponseSignal.RAG_ANSWER_ERROR.value,
                "message": f"No answer found for the query in project {project_id}."
            }
        )

    return JSONResponse(
        status_code= status.HTTP_200_OK,
        content= {
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "message": f"Answer generated for project {project_id}.",
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )
