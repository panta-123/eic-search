from typing import List, Any
from pydantic import BaseModel, Extra

class Dataset(BaseModel):
    scope: str
    name: str
    campaign: str
    detector_config: str
    physics_process: str
    generator: str
    collision: str
    q2: str
    description: str

    class Config:
        extra = Extra.forbid

class DistinctFieldValuesResponse(BaseModel):
    values: List[Any]
