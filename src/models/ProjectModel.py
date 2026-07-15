from .BaseDataModel import BaseDataModel
from .db_schemes import ProjectEntry
from .enums.DataBaseEnum import DataBaseEnum

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client) 
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    async def create_project(self, project: ProjectEntry):
        result = await self.collection.insert_one(
            project.model_dump(by_alias=True, exclude_unset=True)
            )
        project.id = result.inserted_id

        return project
    
    async def get_or_create_project(self, project_id:str):
        record = await self.collection.find_one({
            "project_id": project_id
        })

        if record is None:
            # create new
            project = ProjectEntry(project_id=project_id)
            return await self.create_project(project)
        
        return ProjectEntry(**record)
    
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        total_records = await self.collection.count_documents({})

        total_pages = (total_records + page_size - 1) // page_size

        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        projects = [ProjectEntry(**record) async for record in cursor]

        return projects, total_pages
    
    









