from fastapi import Depends, APIRouter, HTTPException, status
from app.models import Dataset
from app.elasticsearch.config import ELASTICSEARCH_INDEX
from elasticsearch import Elasticsearch, exceptions
from typing import List
INDEX_NAME = ELASTICSEARCH_INDEX
router = APIRouter()


def get_es_client():
    # Get instance from main.py (dependency injection)
    return Depends(lambda: app.es)

@router.post("/create", response_model=Dataset)
async def create_dataset(data: Dataset, es: Elasticsearch = Depends(get_es_client)):
    try:
        data.id = data.get_id()  # Assuming this generates ID

        # Check if document exists already
        if es.exists(index=INDEX_NAME, id=data.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dataset with the same scope and name already exists",
            )

        # Create document in Elasticsearch
        res = es.index(index=INDEX_NAME, id=data.id, document=data.dict())
        return data

    except exceptions.ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error connecting to Elasticsearch: " + str(e),
        )
    except exceptions.ElasticsearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error indexing dataset: " + str(e),
        )

@router.delete("/delete/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(id: str, es: Elasticsearch = Depends(get_es_client)):
    try:
        # Delete document from Elasticsearch
        es.delete(index=INDEX_NAME, id=id)
    except exceptions.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    except exceptions.ElasticsearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting dataset: " + str(e),
        )

@router.put("/update/{id}", response_model=Dataset)
async def update_dataset(id: str, data: Dataset, es: Elasticsearch = Depends(get_es_client)):
    try:
        # Update document in Elasticsearch
        es.update(index=INDEX_NAME, id=id, doc=data.dict())

        # Fetch updated document for response
        updated_data = es.get(index=INDEX_NAME, id=id)
        return updated_data

    except exceptions.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    except exceptions.ElasticsearchException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating dataset: " + str(e),
        )

@router.get("/search/{query}")
async def search(query: str):
    results = es.search(
        index="dataset_index",  # Replace with your actual index name
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["metadata.name", "metadata.description", "metadata.other_fields"]  # Adjust as needed
                }
            }
        }
    )
    return await Dataset.parse_obj(results)  # Process and return results


