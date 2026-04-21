from pydantic import BaseModel
from typing import Optional, List

class ArchitectureRequest(BaseModel):
    user_requirement: str
    invention_id: str

class ArchitectureResponse(BaseModel):
    status: str
    mermaid_code: Optional[str] = None
    svg_url: Optional[str] = None
    message: Optional[str] = None
