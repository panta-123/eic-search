"""
CRUD operations
"""
from fastapi import Depends, APIRouter, HTTPException, status, Body
from app.models.dataset import Dataset
from app.elasticsearch.config import OPENSEARCH_INDEX
from app.elasticsearch.mapping import create_index_if_not_exists
from opensearchpy import OpenSearch, exceptions
from opensearchpy.helpers import bulk
from app.logging.logger import logger

from typing import List, Dict
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
            print(dataset)
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
    

@router.post("/search")
async def search(query: Dict= Body(...), es: OpenSearch = Depends(get_es_client)):
    must_list = []
    for key, value in query.items():
        must_list.append({"match": {key: value}})

    results = es.search(
        index=OPENSEARCH_INDEX,
        body={
            "query": {
                "bool": {
                    "must": must_list
                }
            }
        }
    )
    hits = results.get('hits', {}).get('hits', [])
    source_list = [hit['_source'] for hit in hits]
    return source_list # Process and return results

@router.get("/mapping")
async def get_opensearch_mapping(es: OpenSearch = Depends(get_es_client)):
    try:
        mapping_data = es.indices.get_mapping(INDEX_NAME)
        return mapping_data[INDEX_NAME]["mappings"]["properties"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting mapping: {str(e)}")