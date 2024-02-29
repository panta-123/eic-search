from pydantic import BaseModel

class Dataset(BaseModel):
    scope: str
    name: str
    campaign: str
    detector_config: str
    physics_process: str
    generator: str
    collision: str
    q2: str
    dataset: str
    description: str