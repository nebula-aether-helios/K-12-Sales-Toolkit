from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DatasetOut(BaseModel):
    id: int
    source: str
    source_id: str
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    last_updated: Optional[str]
    tags: Optional[List[str]]


class DatasetCreate(BaseModel):
    source: str
    source_id: str
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    schema: Optional[Dict[str, Any]]
    raw_metadata: Optional[Dict[str, Any]]


class PreviewOut(BaseModel):
    dataset_id: int
    rows: List[Dict[str, Any]]
