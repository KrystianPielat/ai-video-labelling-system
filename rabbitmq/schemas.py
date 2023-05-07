from pydantic import BaseModel
from typing import List


class Container(BaseModel):
    name: str
    status: str
    image: str
    created: str


class ContainerList(BaseModel):
    list: List[Container] = []
