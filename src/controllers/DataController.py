from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models.enums.ResponseEnums import ResponseSignal
import re
import os

class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale=1048576

    # upload file validation
    def validate_uploaded_file(self, file: UploadFile):
        # Validate file type
        # print(file.content_type)
        if file.content_type not in self.app_setting.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        
        # Validate file size
        if file.size > self.app_setting.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value
    
    # Clean org file name
    def get_clean_fileName(self, org_file_name:str):
        # Remove special characters and spaces from the file name
        clean_file_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', org_file_name)
        return clean_file_name
    
    # generate file path
    def generate_file_path(self, org_file_name:str, project_id:str):
        random_str = self.generate_random_string(8)
        project_path = ProjectController().get_project_path(project_id)
        clean_file_name = self.get_clean_fileName(org_file_name)
        new_file_name = os.path.join(project_path, random_str+"_"+clean_file_name)

        while os.path.exists(new_file_name):
            random_str = self.generate_random_string(8)
            new_file_name = os.path.join(project_path, random_str+"_"+clean_file_name)

        return new_file_name, random_str+"_"+clean_file_name

