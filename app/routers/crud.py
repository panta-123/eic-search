"""
CRUD operations
"""
from fastapi import Depends, APIRouter, HTTPException, status
from app.models.dataset import Dataset
from app.elasticsearch.config import OPENSEARCH_INDEX
from app.elasticsearch.mapping import create_index_if_not_exists
from opensearchpy import OpenSearch, exceptions
from opensearchpy.helpers import bulk
from app.logging.logger import logger

from typing import List
from app.elasticsearch.config import (
    OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD
)
from fastapi.encoders import jsonable_encoder

INDEX_NAME = OPENSEARCH_INDEX
router = APIRouter()

logger.debug("router API...")

def get_es_client():
    return OpenSearch(
        hosts = [{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
        http_auth = (OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
        use_ssl = True,
        verify_certs = False
        )


@router.post("/create", status_code=201)
async def create_dataset(datasets: List[Dataset], es: OpenSearch = Depends(get_es_client)):
    create_index_if_not_exists(es=es)
    try:
        actions = []
        for dataset in datasets:
            _id = f"{dataset.scope}:{dataset.name}"  # Generate ID based on scope and name

            # Check if document exists already
            if es.exists(index=INDEX_NAME, id=_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Dataset with ID {_id} already exists",
                )
            actions.append({    
                    "_index": INDEX_NAME,
                    "_id": _id,
                    "_source": jsonable_encoder(dataset),
                    "_op_type": "index"
                })
        bulk(es, actions)
        return {"message": "Datasets created successfully!"}
    except Exception as e:
        # Handle and log exceptions
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{_id}")  # Remove explicit status code
async def delete_dataset(_id: str, es: OpenSearch = Depends(get_es_client)):
    try:
        es.delete(index=INDEX_NAME, id=_id)
        return True  # Return True on success
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dataset: {str(e)}")

@router.put("/update/{_id}")
async def update_dataset(_id: str, data: Dataset, es: OpenSearch = Depends(get_es_client)):
    try:
        es.update(index=INDEX_NAME, id=_id, body= {"doc": jsonable_encoder(data)})
        updated_data = es.get(index=INDEX_NAME, id=_id)
        return updated_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dataset: {str(e)}")
    

@router.get("/search/{query}")
async def search(query: str, es: OpenSearch = Depends(get_es_client)):
    results = es.search(
        index=OPENSEARCH_INDEX,  # Replace with your actual index name
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

