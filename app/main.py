"""
main 
"""
from fastapi import FastAPI, Response, FastAPI, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from app.models.dataset import Dataset
from app.routers import crud, distinct
from app.logging.logger import logger
from opensearchpy import OpenSearch

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message


app = FastAPI(
    title="Opensearch API",
    description="API for searching the 'scope:name' dataset using metadata in Opensearch",
)
logger.info("OPENSEARCH API...")
origins = ["*"]
app.add_middleware(
   CORSMiddleware,
   allow_origins=origins,
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

app.include_router(crud.router, prefix="/search")
app.include_router(distinct.router, prefix="/agg")

