from app.routers.crud import get_es_client, INDEX_NAME
from opensearchpy import OpenSearch, exceptions
from opensearchpy.helpers import bulk
from app.logging.logger import logger
from fastapi import Depends, APIRouter, HTTPException, status
from app.models.dataset import DistinctFieldValuesResponse

router = APIRouter()

@router.get("/getDistinctValues/{field}", response_model=DistinctFieldValuesResponse)  # Remove explicit status code
async def get_distinct_values(field: str, es: OpenSearch = Depends(get_es_client)):
    try:
        query = {
                "aggs": {
                    "keys": {
                    "terms": {
                        "field": f"{field}"
                    }
                    }
                },
                "size": 0
        }
        response = es.search(body = query, index = INDEX_NAME)
        keys = response["aggregations"]["keys"]["buckets"]
        return DistinctFieldValuesResponse(values=[key["key"] for key in keys])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating dataset: {str(e)}")
