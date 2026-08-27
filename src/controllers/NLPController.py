from .BaseController import BaseController
from models.db_schemes import ProjectEntry, DataChunkEntry
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json
from stores.llm.templates.template_parser import TemplateParser

class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client,
                 embedding_client, template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()

    def reset_vector_db_collection(self, project_id:str):
        collection_name = self.create_collection_name(project_id)
        return self.vectordb_client.delete_collection(collection_name= collection_name)

    def get_vector_db_collection_info(self, project_id: str):
        collection_name = self.create_collection_name(project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name= collection_name)

        print(f"For developement: Collection info:\n {collection_info}")
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )

    def index_into_vector_db(self, project: ProjectEntry,
                             chunks: List[DataChunkEntry],
                             chunks_ids: List[int],
                             do_reset: bool = False):
        
        collection_name = self.create_collection_name(project.project_id)

        texts = [chunk.chunk_text for chunk in chunks]
        metadata = [chunk.chunk_metadata for chunk in chunks]
        vectors = [
            self.embedding_client.embed_text(
                text= text,
                document_type= DocumentTypeEnum.DOCUMENT.value
            )
            for text in texts
        ]

        _ = self.vectordb_client.create_collection(
            collection_name = collection_name,
            embedding_size= self.embedding_client.embedding_size,
            do_rest= do_reset
        )

        _ = self.vectordb_client.insert_many(
            collection_name = collection_name,
            texts= texts,
            vectors= vectors,
            metadata= metadata,
            record_ids= chunks_ids
        )

        return True

    def search_vector_db_collection(self, project: ProjectEntry, 
                                    text: str,
                                    limit: int = 10):
        collection_name = self.create_collection_name(project.project_id)

        vector = self.embedding_client.embed_text(
            text= text,
            document_type= DocumentTypeEnum.QUERY.value
        )

        if not vector or len(vector) == 0:
            print("Failed to generate embedding for the query text.")
            return False

        results = self.vectordb_client.search_by_vector(
            collection_name= collection_name,
            query_vector= vector,
            limit= limit
        )

        if not results:
            print("No results found in the vector database.")
            return False
        return results

    def answer_rag_question(self, project: ProjectEntry, query: str, limit: int = 10):

        retrieved_docs = self.search_vector_db_collection(
            project= project,
            text= query,
            limit= limit
        )

        if not retrieved_docs or len(retrieved_docs) == 0:
            print("No documents retrieved for the given query.")
            return None, None, None

        system_prompt = self.template_parser.get(group= "rag", key= "system_prompt")

        document_prompts = "\n".join([
            self.template_parser.get(group = "rag", key = "document_prompt",
                                     var = {"doc_num":idx+1, 
                                            "chunk_text": doc.text})
                                            for idx, doc in enumerate(retrieved_docs)])

        footer_prompt = self.template_parser.get(group= "rag", key= "footer_prompt")

        chat_history = [
            self.generation_client.construct_prompt(
                role = self.generation_client.enums.SYSTEM.value,
                prompt = system_prompt
            )
        ]

        full_prompt = "\n".join([document_prompts, footer_prompt])

        answer = self.generation_client.generate_text(
            prompt = full_prompt,
            chat_history= chat_history,
        )

        return answer, full_prompt, chat_history




        

        
        
        