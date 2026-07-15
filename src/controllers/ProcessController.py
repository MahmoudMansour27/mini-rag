from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader 
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from models import ProcessingEnums 

class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id)

    def get_file_extension(self, file_id: str) -> str:
        return os.path.splitext(file_id)[1].lower()
    
    def get_file_loader(self, file_id: str):
        file_extension = self.get_file_extension(file_id)
        file_path = os.path.join(self.project_path, file_id)

        if file_extension == ProcessingEnums.TXT.value:
            return TextLoader(file_path)
        elif file_extension == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)
        
        return None
    
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id)
        if loader is None:
            return None

        documents = loader.load()

        return documents
    
    def process_file_content(self, file_content: list, 
                             file_id: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            length_function=len
            )
        try:
            chunks = text_splitter.split_documents(file_content)
        except Exception as e:
            return None

        return chunks
    



