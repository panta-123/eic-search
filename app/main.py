# app/main.py

from fastapi import FastAPI, Depends, FastAPI, HTTPException, Security, status
from app.models import Dataset
from app.routers import crud
from app.elasticsearch.config import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_PORT,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_PASSWORD,
)
from app.elasticsearch.mapping import create_index_if_not_exists

from elasticsearch import Elasticsearch

# Create the Elasticsearch client using imported configuration
es = Elasticsearch(
    host=ELASTICSEARCH_HOST,
    port=ELASTICSEARCH_PORT,
    basic_auth=(ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD) if ELASTICSEARCH_USERNAME else None,
)
create_index_if_not_exists(es)


app = FastAPI(
    title="Elasticsearch Search API",
    description="API for searching the 'scope:name' dataset using metadata in Elasticsearch",
)
app.es = es

app.include_router(crud.router, prefix="/search")
