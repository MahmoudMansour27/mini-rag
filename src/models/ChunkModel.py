from .BaseDataModel import BaseDataModel
from .db_schemes.data_chunk import DataChunkEntry
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
            indexes = DataChunkEntry.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name= index["name"],
                    unique= index["unique"]
                )

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

    async def get_project_chunks(self, project_id: ObjectId, page_no: int=1, page_size: int=50):
        records = await self.collection.find({
            "chunk_project_id": project_id
        }).skip(
            (page_no - 1) * page_size
        ).limit(
            page_size
        ).to_list(length= None)

        return [
            DataChunkEntry(**record) for record in records
        ]
            
        
        