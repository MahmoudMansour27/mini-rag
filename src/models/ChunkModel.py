from .BaseDataModel import BaseDataModel
from .db_schemes.data_chunk import DataChunkEntry
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    async def create_chunk(self, chunk: DataChunkEntry):
        result = await self.collection.insert_one(
            chunk.model_dump(by_alias=True, exclude_unset=True))
        chunk.id = result.inserted_id
        return chunk
    
    async def get_chunk(self, chunk_id: str):
        result = await self.collection.find_one(
            {
                "_id": ObjectId(chunk_id)
            }
        )
        if result is None:
            return None
        return DataChunkEntry(**result)
    
    async def create_many_chunks(self, chunks: list, batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            requests = [InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True)) for chunk in batch]
            await self.collection.bulk_write(requests)
        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many(
            {
                "chunk_project_id": project_id
            }
        )
        return result.deleted_count
        